FROM frappe/erpnext:v16.33.0
COPY --chown=frappe:frappe phase0/localization/patches /opt/phase0-zh-patches
ARG APPLY_ZH_SOURCE_PATCHES=1
RUN case "$APPLY_ZH_SOURCE_PATCHES" in \
      1) env/bin/python /opt/phase0-zh-patches/patch_core.py ;; \
      0) env/bin/python /opt/phase0-zh-patches/patch_core.py --check ;; \
      *) exit 1 ;; \
    esac
COPY --chown=frappe:frappe apps/erpnext_zh /home/frappe/frappe-bench/apps/erpnext_zh
RUN /home/frappe/frappe-bench/env/bin/pip install --no-deps -e /home/frappe/frappe-bench/apps/erpnext_zh
COPY --chown=frappe:frappe phase0/localization/apps.txt /home/frappe/frappe-bench/sites/apps.txt
RUN bench build --apps frappe,erpnext,erpnext_zh --force \
    && cp -a sites/assets/erpnext_zh assets/erpnext_zh \
    && if [ ! sites/assets/assets.json -ef assets/assets.json ]; then cp sites/assets/assets.json assets/assets.json; fi
