"use strict";

var ItemCardLoaded = true;

class Widget_ItemCard extends Widget_OakHUDWidgetBase {
	constructor() {
		super();
	}

	connectedCallback() {
		super.connectedCallback();
	}

	Init() {
		super.Init();

		this.DamageType1 = "";
		this.ElementIconWrapper1 = null;
		this.ElementIcon1 = null;

		this.DamageType2 = "";
		this.ElementIconWrapper2 = null;
		this.ElementIcon2 = null;

		this.initialized = false;

		this.tooltip = this.querySelector(".tooltip_container");

		this.tool_tip_width = 0;
		this.tool_tip_height = 0;

		this.ItemBaseType = "";

		this.UpdateRAF = null;
	}

	RegisterEvents() {
		super.RegisterEvents();
		this.RegisterWidgetEvent("UpdateVisibility", this.UpdateVisibility.bind(this));
	}

	UpdateVisibility(value) {
		if (this.tooltip) {
			this.tooltip.UpdateShowTooltipStatus(value);
		}
	}

	Event_DataUpdated() {
		super.Event_DataUpdated();

		if (this.DataModel === undefined) return;

		if (!this.initialized) {
			if (this.DataModel && this.DataModel.abbreviated) {
				this.ElementIconWrapper1 = this.querySelector(".abbr_element1");
				this.ElementIconWrapper2 = this.querySelector(".abbr_element2");
			}

			if (this.DataModel && this.DataModel.itemcardshowdelay >= 0) {
				TooltipMgr.TooltipShowDelay = this.DataModel.itemcardshowdelay;
			}

			this.initialized = true;
		}

		this.UpdateDamageType();

		this.tooltipRect = this.getBoundingClientRect();
		if (this.tooltip) {
			this.tooltipRect = this.tooltip.getBoundingClientRect();
			this.tooltip.bDoubleTooltip = this.DataModel.comparemode;
		}

		if (!this.DataModel.mousepositioned) {
			this.ClearCurrentRAF();
			this.RecalculateLocation();
		}
	
		if (this.tooltipRect) {
			this.tool_tip_width = this.tooltipRect.width;
			this.tool_tip_height = this.tooltipRect.height;
		}

		// Custom tool tip event
		if (this.DataModel.mousepositioned && this.TooltipElement === undefined) {
			this.SetTooltipCallbacks();
		}
	}

	Event_Deactivate() {
        super.Event_Deactivate();
		if (this.tooltip) {
			this.tooltip.UpdateShowTooltipStatus(false);
		}
    }

	BeginActivate()
    {
        super.BeginActivate();

		this.StartUpdateRAF();
    }

	BeginDeactivate()
    {
		cancelAnimationFrame(this.UpdateRAF);
		super.BeginDeactivate();
	}

	StartUpdateRAF()
	{
		this.ClearCurrentRAF();

		this.UpdateRAF = requestAnimationFrame(() => this.RecalculateLocation());
	}

	ClearCurrentRAF()
	{
		if (this.UpdateRAF) {
			cancelAnimationFrame(this.UpdateRAF);
			this.UpdateRAF = null;
		}
	}

	RecalculateLocation() {
		if (this.DataModel === undefined) return;
		if (this.DataModel.mousepositioned || window.innerHeight <= 0.0) return;

		var tooltipRectElement = this.querySelector(".item_card_bkg_cntr");
		this.tooltipRect = tooltipRectElement.getBoundingClientRect();

		if (this.tooltipRect) {
			this.tool_tip_width = this.tooltipRect.width;
			this.tool_tip_height = this.tooltipRect.height;
		}

		const horizontal_units = this.DataModel.positionunits || "vw";
		const vertical_units = this.DataModel.positionunits || "vh";

		const card_screen_height = (this.tool_tip_height / window.innerHeight) * 100.0;
		const card_top = this.DataModel.posy - card_screen_height;
		var card_bottom = this.DataModel.posy;

		if (card_top < this.DataModel.clampedheightoftopofitemcard) {
			card_bottom = this.DataModel.clampedheightoftopofitemcard + card_screen_height;
		
			if (card_bottom > this.DataModel.itemposy) {
				card_bottom = this.DataModel.itemposy;
			}
		}

		if (card_bottom > 100 && !this.DataModel.abbreviated) {
			card_bottom = 100;
		}

		this.style.transform = `translate(${this.DataModel.posx}${horizontal_units},${card_bottom}${vertical_units}) scale(${this.DataModel.scale})`;
		
		this.StartUpdateRAF();
	}

	UpdateDamageType() {
		if (this.DataModel.cardisflipped) {
			// Reset damage types on flip so they refresh when shown again
			this.DamageType1 = "";
			this.DamageType2 = "";
			return;
		}

		let bShowFirstIcon = (this.DataModel.damagetype1 != "");
		var ElementChanged = false;

		if (this.DamageType1 != this.DataModel.damagetype1 || this.ItemBaseType != this.DataModel.itembasetype) {
			ElementChanged = true;
			this.ElementIconWrapper1 = this.querySelector(".item_card_element1");

			if (this.ElementIconWrapper1) {
				this.ElementIcon1 = this.ElementIconWrapper1.querySelector("elemental-damagetype");
				this.ElementIcon1.SetWidget(this);
				this.DamageType1 = this.DataModel.damagetype1;
			}

			if (this.ElementIcon1) {
				if (bShowFirstIcon) {
					this.ElementIcon1.SetElement(this.DamageType1);
					this.ElementIcon1.SetFrame(true);
					this.ElementIcon1.Show();
				}
				else {
					this.ElementIcon1.Hide();
				}
			}
		}

		let bShowSecondIcon = (this.DataModel.damagetype2 != "") && (this.DataModel.damagetype1 != this.DataModel.damagetype2);
		if (this.DamageType2 != this.DataModel.damagetype2 || this.ItemBaseType != this.DataModel.itembasetype) {
			ElementChanged = true;
			this.ElementIconWrapper2 = this.querySelector(".item_card_element2");

			if (this.ElementIconWrapper2) {
				this.ElementIcon2 = this.ElementIconWrapper2.querySelector("elemental-damagetype");
				this.ElementIcon2.SetWidget(this);
				this.DamageType2 = this.DataModel.damagetype2;
			}

			if (this.ElementIcon2) {
				if (bShowSecondIcon) {
					this.ElementIcon2.SetElement(this.DamageType2);
					this.ElementIcon2.SetFrame(true);
					this.ElementIcon2.Show();
				}
				else {
					this.ElementIcon2.Hide();
				}
			}
		}

		if (ElementChanged) {
			this.ItemBaseType = this.DataModel.itembasetype;
			if (this.DataModel.damagetype1 != "impact") {
				this.SetDamageTypePresentation(1);
			}
			else {
				this.SetDamageTypePresentation(2);
			}
			
			if (this.ResetHandle != null) { clearTimeout(this.ResetHandle); }

			// Switch between showing both elements
			if (bShowFirstIcon && bShowSecondIcon && this.DataModel.damagetype1 != "impact" && this.DataModel.damagetype2 != "impact") {
				this.ResetHandle = setTimeout(() => { this.AlternateDamageTypes(); }, this.DataModel.elementswapdelay * 1000.0);
			}
		}
	}

	SetDamageTypePresentation(slot) {
		this.ElementSlot = slot;
		var ElementBacking = this.querySelector(".ic_element_backing");
		var ElementText = this.querySelector(".item_card_element_text");

		var DamageTypeClass = "";
		var ElementTextMarkup = "";
		if (slot == 1) {
			if (this.DataModel.damagetype1 == "") return;
			DamageTypeClass = this.DataModel.damagetype1;
			ElementTextMarkup = MarkupMgr.ResolveMarkupText(this.DataModel.elementtext);
		}
		if (slot == 2) {
			if (this.DataModel.damagetype2 == "") return;
			DamageTypeClass = this.DataModel.damagetype2;
			ElementTextMarkup = MarkupMgr.ResolveMarkupText(this.DataModel.secondelementtext);
		}

		if (ElementBacking && this.DataModel.damagetype1 != "") {
			ElementBacking.className = "ic_element_backing " + DamageTypeClass;
		}
		if (ElementText && this.DataModel.damagetype1 != "") {
			ElementText.innerHTML = ElementTextMarkup;
			ElementText.className = "item_card_element_text " + DamageTypeClass;
		}
	}

	AlternateDamageTypes() {
		if (this.ElementSlot == 1) {
			this.SetDamageTypePresentation(2);
		}
		else {
			this.SetDamageTypePresentation(1);
		}
		this.ResetHandle = setTimeout(() => { this.AlternateDamageTypes(); }, this.DataModel.elementswapdelay * 1000.0);
	}

	SetTooltipCallbacks() {
		this.TooltipElement = this.querySelector("#item_card_tooltip");
		if (this.TooltipElement === undefined) return;

		this.functionOnTooltipFocusedCallback = (e) => this.OnTooltipFocusedCallback(e);
		this.functionOnTooltipUnfocusedCallback = (e) => this.OnTooltipUnfocusedCallback(e);

		document.addEventListener('Event_ItemTooltipFocused', this.functionOnTooltipFocusedCallback);
		document.addEventListener('Event_ItemTooltipUnfocused', this.functionOnTooltipUnfocusedCallback);

		if (this.DataModel.compare) {
			this.TooltipElement.bDoubleOffset = true;
		}

		this.tooltipCallbackSet = true;
	}

	OnTooltipFocusedCallback(eventData) {
		if (this.TooltipElement === undefined) return;

		if (eventData.detail.infoData.focusedElement) {
			this.TooltipElement.SetFocusedElementInfo(eventData.detail.infoData.focusedElement);
			this.TooltipElement.UpdatePosition();
		}

		this.TooltipElement.tooltipScale = 1;
	}

	OnTooltipUnfocusedCallback(eventData) {
		if (this.TooltipElement === undefined) return;

		this.TooltipElement.ClearFocusedElementInfo();
	}
}
window.customElements.define('widget-item-card', Widget_ItemCard);