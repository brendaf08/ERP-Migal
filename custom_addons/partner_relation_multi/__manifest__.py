{
    'name': 'Múltiples Relaciones entre Contactos',
    'version': '19.0.1.0.3',
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
* Las asociaciones nuevas se guardan en el sentido en que se agregan.
* La ficha permite seleccionar contactos o empresas existentes.
* Los vínculos ya guardados se conservan, incluidos los pares creados por la
  versión bidireccional.
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
    'installable': True,
    'auto_install': False,
    'application': False,
}
