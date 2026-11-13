FROM odoo:19.0@sha256:27f920e002c43a1af7022a68f3cc17db71a2f9f3348800cb050721ce54893e49

LABEL org.opencontainers.image.source="https://github.com/brendaf08/ERP-Migal"

USER root
COPY infra/odoo/requirements.txt /tmp/migal-requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages \
    -r /tmp/migal-requirements.txt
RUN sed -i 's|^addons_path = .*|addons_path = /opt/migal/addons|' /etc/odoo/odoo.conf
COPY --chown=odoo:odoo custom_addons/ /opt/migal/addons/
USER odoo
