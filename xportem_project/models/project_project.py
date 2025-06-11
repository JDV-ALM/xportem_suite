# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'
    
    # Computed Fields for Client Metrics
    x_client_code = fields.Char(
        string='Código Cliente',
        related='partner_id.x_client_code',
        readonly=True,
        store=True,
        help='Código único del cliente desde el contacto'
    )
    
    x_total_requests = fields.Integer(
        string='Total Solicitudes',
        compute='_compute_client_metrics',
        store=False,
        help='Número total de solicitudes del cliente'
    )
    
    x_active_requests = fields.Integer(
        string='Solicitudes Activas',
        compute='_compute_client_metrics',
        store=False,
        help='Número de solicitudes actualmente en proceso'
    )
    
    x_completed_requests = fields.Integer(
        string='Solicitudes Completadas',
        compute='_compute_client_metrics',
        store=False,
        help='Número de solicitudes completadas'
    )
    
    x_total_savings = fields.Monetary(
        string='Ahorro Total',
        compute='_compute_financial_metrics',
        store=False,
        currency_field='currency_id',
        help='Ahorro acumulado en todas las compras'
    )
    
    x_avg_cycle_time = fields.Float(
        string='Tiempo Promedio (días)',
        compute='_compute_time_metrics',
        store=False,
        digits=(6, 1),
        help='Tiempo promedio de ciclo de procura en días'
    )
    
    # Configuration Fields
    x_auto_create_stages = fields.Boolean(
        string='Auto-crear Etapas',
        default=True,
        help='Crear automáticamente las etapas estándar de procura al crear el proyecto'
    )
    
    # ===== Compute Methods =====
    @api.depends('task_ids', 'task_ids.stage_id')
    def _compute_client_metrics(self):
        """Calcular métricas básicas del cliente"""
        for project in self:
            tasks = project.task_ids
            project.x_total_requests = len(tasks)
            
            # Considerar activas las que no están en etapa final
            done_stages = tasks.mapped('stage_id').filtered(lambda s: s.fold)
            active_tasks = tasks.filtered(lambda t: t.stage_id not in done_stages)
            project.x_active_requests = len(active_tasks)
            project.x_completed_requests = len(tasks) - len(active_tasks)
    
    @api.depends('task_ids')
    def _compute_financial_metrics(self):
        """Calcular métricas financieras"""
        for project in self:
            # Por ahora, establecer en 0. Se implementará cuando tengamos el sistema de cotizaciones completo
            project.x_total_savings = 0.0
    
    @api.depends('task_ids', 'task_ids.date_deadline', 'task_ids.create_date')
    def _compute_time_metrics(self):
        """Calcular métricas de tiempo"""
        for project in self:
            completed_tasks = project.task_ids.filtered(
                lambda t: t.stage_id.fold and t.date_deadline and t.create_date
            )
            
            if completed_tasks:
                total_days = sum(
                    (task.date_deadline - task.create_date.date()).days 
                    for task in completed_tasks
                )
                project.x_avg_cycle_time = total_days / len(completed_tasks)
            else:
                project.x_avg_cycle_time = 0.0
    
    # ===== Override Methods =====
    @api.model_create_multi
    def create(self, vals_list):
        """Override para configuración automática"""
        projects = super().create(vals_list)
        
        for project in projects:
            # Validar que el partner sea un cliente de procura
            if project.partner_id and not project.partner_id.x_is_procurement_client:
                raise UserError(
                    self.env._('El contacto seleccionado debe ser un cliente de procura.')
                )
            
            # Crear etapas estándar si está habilitado
            if project.x_auto_create_stages:
                project._create_default_stages()
        
        return projects
    
    def write(self, vals):
        """Override para validaciones en actualización"""
        if 'partner_id' in vals and vals['partner_id']:
            partner = self.env['res.partner'].browse(vals['partner_id'])
            if not partner.x_is_procurement_client:
                raise UserError(
                    self.env._('El contacto seleccionado debe ser un cliente de procura.')
                )
        
        return super().write(vals)
    
    # ===== Business Methods =====
    def _create_default_stages(self):
        """Crear las etapas estándar del proceso de procura"""
        self.ensure_one()
        
        # Verificar si ya tiene etapas
        if self.type_ids:
            return
        
        # Definir etapas estándar
        stages_data = [
            {
                'name': 'Solicitud Recibida',
                'sequence': 10,
                'fold': False,
            },
            {
                'name': 'Búsqueda de Proveedores',
                'sequence': 20,
                'fold': False,
            },
            {
                'name': 'Cotizando',
                'sequence': 30,
                'fold': False,
            },
            {
                'name': 'Evaluación',
                'sequence': 40,
                'fold': False,
            },
            {
                'name': 'Aprobación Cliente',
                'sequence': 50,
                'fold': False,
            },
            {
                'name': 'En Compra',
                'sequence': 60,
                'fold': False,
            },
            {
                'name': 'En Tránsito',
                'sequence': 70,
                'fold': False,
            },
            {
                'name': 'Entregado',
                'sequence': 80,
                'fold': True,
            },
            {
                'name': 'Cancelado',
                'sequence': 90,
                'fold': True,
            },
        ]
        
        # Crear las etapas
        stages = self.env['project.task.type']
        for stage_vals in stages_data:
            stage = stages.create({
                'name': stage_vals['name'],
                'sequence': stage_vals['sequence'],
                'fold': stage_vals['fold'],
                'project_ids': [(4, self.id)],
            })
            stages |= stage
        
        return stages
    
    def action_view_active_requests(self):
        """Acción para ver solicitudes activas"""
        self.ensure_one()
        
        done_stages = self.task_ids.mapped('stage_id').filtered(lambda s: s.fold)
        active_tasks = self.task_ids.filtered(lambda t: t.stage_id not in done_stages)
        
        action = {
            'name': f'Solicitudes Activas - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', active_tasks.ids)],
            'context': {
                'default_project_id': self.id,
                'search_default_project_id': self.id,
            },
        }
        
        return action
    
    def action_view_all_requests(self):
        """Acción para ver todas las solicitudes del proyecto"""
        self.ensure_one()
        
        action = {
            'name': f'Todas las Solicitudes - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'kanban,list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'search_default_project_id': self.id,
            },
        }
        
        return action
    
    def action_create_request(self):
        """Acción para crear nueva solicitud"""
        self.ensure_one()
        
        # Obtener la primera etapa
        first_stage = self.type_ids.sorted('sequence')[0] if self.type_ids else False
        
        action = {
            'name': 'Nueva Solicitud',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'form',
            'context': {
                'default_project_id': self.id,
                'default_stage_id': first_stage.id if first_stage else False,
                'default_x_is_request': True,
            },
        }
        
        return action