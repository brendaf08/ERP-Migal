FROM odoo:19
USER root
RUN pip install --no-cache-dir --break-system-packages qifparse==0.5
COPY iniciar.py /opt/migal/iniciar.py
COPY filestore.py /opt/migal/filestore.py
COPY restaurar_respaldo.py /opt/migal/restaurar_respaldo.py
USER odoo
ENTRYPOINT ["python3", "/opt/migal/iniciar.py"]
CMD ["odoo"]
