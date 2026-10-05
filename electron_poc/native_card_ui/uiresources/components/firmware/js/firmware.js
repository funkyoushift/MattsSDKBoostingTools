"use strict";

class FirmwareComponent extends GbxCustomElement
{
	constructor()
    {
		super();
	}

	Init() {
		super.Init();
		this.Widget = undefined;
		this.DataModel = undefined;
	}

	Activate() {
        super.Activate();
		this.Firmwarepips = this.querySelectorAll(".firmware_bonus_piece");
	}

	UpdateData() {
		if (this.DataModel === undefined) return;

		this.Firmwarepips?.forEach((element, idx) => {
			let currentpip = idx + 1;
			element.classList.toggle("active",this.DataModel.firmwarecount >= currentpip);
			element.classList.toggle("empty",this.DataModel.firmwarecount < currentpip);
		});
	}

	SetWidget(Widget) {
		this.Widget = Widget;
	}

	SetDataModel(Model) {
		this.DataModel = Model;
		this.UpdateData();
	}
};
window.customElements.define('firmware-segments', FirmwareComponent);
