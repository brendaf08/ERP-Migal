{
    'name': 'Múltiples Relaciones entre Contactos',
    'version': '19.0.1.0.1',
    'summary': 'Asocia un mismo contacto con múltiples contactos o empresas',
    'description': """
Múltiples Relaciones entre Contactos
====================================

Este módulo añade una relación muchos a muchos (Many2many) independiente entre
registros de ``res.partner``, permitiendo que un mismo contacto esté asociado
simultáneamente a varios contactos o empresas.

Características principales
---------------------------

* Un contacto puede estar asociado a múltiples contactos o empresas a la vez.
* La relación es realmente bidireccional: si asocias una persona con una
  empresa, la empresa aparece en la ficha de la persona y la persona aparece
  en la ficha de la empresa.
* Se muestra como una sección tipo «Contactos», con tarjetas, alta y edición
  inline y posibilidad de seleccionar contactos o empresas existentes.
* No crea duplicados de ``res.partner``.
* Es totalmente independiente de la relación estándar de empresa matriz
  (``parent_id`` / ``child_ids``), que no se modifica.
* Impide asociar un contacto consigo mismo.
* La tabla relacional evita asociaciones duplicadas de forma automática.
""",
    'author': 'Custom Development',
    'license': 'AGPL-3',
    'category': 'CRM',
    'depends': ['base'],
    'data': [
        'views/partner_relation_multi_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
    'application': False,
}
