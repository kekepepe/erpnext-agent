/* Offline contract checks for native presentation hooks; no browser or ERP writes. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const hooks = new Map();
const translations = {'P0 Claw Hammer': '测试羊角锤', 'To Receive and Bill': '待收货及开票'};
const context = {
    document: {}, Node: {TEXT_NODE: 3},
    $: () => ({ready: fn => fn()}),
    __: value => translations[value] || value,
    frappe: {
        boot: {lang: 'zh'},
        form: {link_formatters: {Item: (value, doc) => doc.item_name ? value + ': ' + doc.item_name : value}},
        utils: {escape_html: text => String(text).replaceAll('<', '&lt;').replaceAll('>', '&gt;')},
        ui: {form: {on: (dt, events) => hooks.set(dt, events)}},
        call: async () => ({message: '壹佰伍拾贰元整'}),
    },
};
vm.runInNewContext(fs.readFileSync('apps/erpnext_zh/erpnext_zh/public/js/form_display.js', 'utf8'), context);
const format = context.frappe.form.link_formatters.Item;
const row = {item_name: 'P0 Claw Hammer', item_code: 'P0-HT-HAMMER'};
assert.equal(format(row.item_code, row, {}), 'P0-HT-HAMMER: 测试羊角锤');
assert.equal(row.item_name, 'P0 Claw Hammer');
assert.equal(format('PRIVATE-1', {item_name: '<private user text>'}, {}), 'PRIVATE-1: <private user text>');
(async () => {
    const doc = {name: 'PUR-ORD-1', currency: 'CNY', rounded_total: 152, grand_total: 152, in_words: 'stored English'};
    const saved = JSON.stringify(doc);
    const field = {df: {}, disp_area: {}, refresh() {this.rendered = this.df.formatter(doc.in_words, this.df, {}, doc);}};
    const frm = {doc, fields_dict: {in_words: field}};
    await hooks.get('Purchase Order').refresh(frm);
    assert.equal(field.rendered, '壹佰伍拾贰元整');
    assert.equal(JSON.stringify(doc), saved);
    assert.equal(field.df.formatter('another document', {}, {}, {...doc, name:'OTHER'}), 'another document');
    assert.equal(field.df.formatter('changed amount', {}, {}, {...doc, rounded_total:0}), 'changed amount');
    assert.equal(field.df.formatter('<private>', {}, {}, {...doc, currency:'USD'}), '&lt;private&gt;');
    // A late reply after navigation must not install another document's formatter.
    const lateField = {df:{}, disp_area:{}, refresh() {throw Error('stale response rendered');}};
    frm.fields_dict.in_words = lateField;
    const pending = hooks.get('Purchase Order').refresh(frm);
    doc.name = 'NEXT';
    await pending;
    assert.equal(lateField.df.formatter, undefined);
    const status = {nodeType:3, textContent:' To Receive and Bill'};
    const privateText = {nodeType:3, textContent:'<private English text>'};
    const item = {dataset:{timestamp:'2026-10-09'}, querySelectorAll:()=>[{childNodes:[status,privateText]}]};
    const timelineFrm = {
        meta:{fields:[{fieldname:'status',options:'To Receive and Bill\nCompleted'}]},
        get_docinfo:()=>({info_logs:[{creation:'2026-10-09', content:'To Receive and Bill'}, {creation:'2026-10-09',content:'<private English text>'}], comments:[{content:'To Receive and Bill'}]}),
        timeline:{wrapper:{find:()=>({each:fn=>fn(0,item)})}},
    };
    hooks.get('Purchase Order').timeline_refresh(timelineFrm);
    assert.equal(status.textContent,' 待收货及开票');
    assert.equal(privateText.textContent,'<private English text>');
    assert.equal(timelineFrm.get_docinfo().comments[0].content,'To Receive and Bill');
    console.log('PASS: item code/title, native money formatter, zero/stale/currency guards, system Info status and private-content preservation');
})().catch(error => { console.error(error); process.exitCode=1; });
