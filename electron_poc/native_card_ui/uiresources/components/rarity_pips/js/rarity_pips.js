"use strict";

class OakRarityPips extends GbxCustomElement
{
    constructor()
    {
        super();
    }

    Init()
    {
        super.Init();
        this.Widget = undefined;
        this.Refresh();
    }

    Refresh()
    {

        if(this.Rarity != undefined)
        {
            this.classList.remove(this.Rarity);
        }

        let NewRarity = this.parentElement.hasAttribute("oak-rarity") ? this.parentElement.getAttribute("oak-rarity") : "";
        if(NewRarity == "" || NewRarity == "none")
        {
            this.Hide();
        }
        else
        {
            this.Show();            
            this.classList.add(NewRarity);
        }

        this.Rarity = NewRarity;
    }

    SetWidget(Widget)
    {
        this.Widget = Widget;
    }

    Show()
    {
        this.classList.remove("invisible");
    }

    Hide()
    {
        this.classList.add("invisible");
    }
};
window.customElements.define('rarity-pips', OakRarityPips);
