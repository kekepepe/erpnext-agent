FROM frappe/erpnext:v16.33.0
COPY --chown=frappe:frappe apps/erpnext_zh /home/frappe/frappe-bench/apps/erpnext_zh
RUN /home/frappe/frappe-bench/env/bin/pip install --no-deps -e /home/frappe/frappe-bench/apps/erpnext_zh
COPY --chown=frappe:frappe phase0/localization/apps.txt /home/frappe/frappe-bench/sites/apps.txt
RUN bench build --app erpnext_zh && cp -a sites/assets/erpnext_zh assets/erpnext_zh
