odoo.define("web_wizard_move.DraggableDialog", function (require) {
"use strict";

var Dialog = require("web.Dialog");

    Dialog.include({

        /* willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Render modal once xml dependencies are loaded
                self.$modal.find('.modal-dialog').draggable();
            });
        }, */

        start: function () {
            // this._super.apply(this, arguments);
            var self = this;
            console.log('called', this);
            this.opened().then(function () {
                self.$el.closest('.modal-dialog').draggable();
            });
            return this._super.apply(this, arguments);
        },
    });
});
