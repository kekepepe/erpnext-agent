FROM frappe/erpnext:v16.33.0
COPY --chown=frappe:frappe phase0/localization/fonts/NotoSansCJKsc-Regular.otf /home/frappe/.local/share/fonts/NotoSansCJKsc-Regular.otf
RUN echo "2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b  /home/frappe/.local/share/fonts/NotoSansCJKsc-Regular.otf" | sha256sum -c - && fc-cache -f
COPY phase0/runtime/frappe.conf.template /templates/nginx/frappe.conf.template
COPY --chown=frappe:frappe phase0/localization/patches /opt/phase0-zh-patches
ARG APPLY_ZH_SOURCE_PATCHES=1
RUN case "$APPLY_ZH_SOURCE_PATCHES" in \
      1) env/bin/python /opt/phase0-zh-patches/patch_core.py ;; \
      0) env/bin/python /opt/phase0-zh-patches/patch_core.py --check ;; \
      *) exit 1 ;; \
    esac
COPY --chown=frappe:frappe phase0/localization/vendor/flit_core-3.12.0-py3-none-any.whl /opt/phase0-build/
RUN echo 'e7a0304069ea895172e3c7bb703292e992c5d1555dd1233ab7b5621b5b69e62c  /opt/phase0-build/flit_core-3.12.0-py3-none-any.whl' | sha256sum -c - \
    && env/bin/pip install --no-index --no-deps /opt/phase0-build/flit_core-3.12.0-py3-none-any.whl
COPY --chown=frappe:frappe apps/erpnext_zh /home/frappe/frappe-bench/apps/erpnext_zh
RUN /home/frappe/frappe-bench/env/bin/pip install --no-index --no-build-isolation --no-deps -e /home/frappe/frappe-bench/apps/erpnext_zh
COPY --chown=frappe:frappe apps/hardware_erp /home/frappe/frappe-bench/apps/hardware_erp
RUN /home/frappe/frappe-bench/env/bin/pip install --no-index --no-build-isolation --no-deps -e /home/frappe/frappe-bench/apps/hardware_erp
COPY --chown=frappe:frappe phase0/localization/apps.txt /home/frappe/frappe-bench/sites/apps.txt
RUN bench build --apps frappe,erpnext,erpnext_zh --force \
    && cp -a sites/assets/erpnext_zh assets/erpnext_zh \
    && if [ ! sites/assets/assets.json -ef assets/assets.json ]; then cp sites/assets/assets.json assets/assets.json; fi
