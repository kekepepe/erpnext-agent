/* Translate only known, hardcoded framework chrome; never business input values. */
$(document).ready(() => {
    if (frappe.boot.lang !== "zh") return;
    const labels = new Map([
        ["Add Sidebar Item", "新增侧栏项目"],
        ["Discard", "放弃更改"],
        ["Save", "保存"],
    ]);
    const localizeSidebarEditor = () => {
        document.querySelectorAll(
            '.body-sidebar .edit-mode .sidebar-item-label, ' +
            '.body-sidebar .discard-button, .body-sidebar .save-sidebar'
        ).forEach(element => {
            const value = labels.get(element.textContent.trim());
            if (value) element.textContent = value;
        });
    };
    // Sidebar rerenders on route changes. This targets fixed framework controls only.
    frappe.router.on("change", localizeSidebarEditor);
    localizeSidebarEditor();
    // Awesomplete bypasses gettext. Limit the observer to its fixed live-region
    // grammar and framework sidebar buttons, never input values or arbitrary text.
    const localizeLibraryChrome = () => {
        localizeSidebarEditor();
        document.querySelectorAll('.form-sidebar .form-title-text > span').forEach(element => {
            const original = element.textContent.trim();
            const translated = __(original);
            if (translated !== original) element.textContent = translated;
        });
        document.querySelectorAll('.awesomplete > span[role="status"]').forEach(element => {
            const original = element.textContent;
            let text = original
                .replace(/^Begin typing for results\.$/, "输入内容以查找结果。")
                .replace(/^Type (\d+) or more characters for results\.$/, "至少输入$1个字符以查找结果。")
                .replace(/^No results found$/, "没有找到结果")
                .replace(/^(\d+) results found$/, "找到$1个结果")
                .replace(/, list item (\d+) of (\d+)$/, "，第$1项，共$2项");
            if (text !== original) element.textContent = text;
        });
    };
    new MutationObserver(localizeLibraryChrome).observe(document.body, {
        childList: true, subtree: true, characterData: true,
    });
    localizeLibraryChrome();
});
