"use strict";

class OakElementDamageType extends GbxCustomElement
{
    constructor()
    {
        super();
    } 

    Init()
    {
        super.Init();
        this.Widget = undefined;
        this.DataModel = undefined;
        this.Element = "fire";
        this.ShowFrame = true;
    }

    SetWidget(Widget)
    {
        this.Widget = Widget;
    }

    SetDataModel(Model)
    {
        this.DataModel = Model;
        this.UpdateData();
    }

    UpdateData()
    {
        if (!this.DataModel) return;

        if (this.DataModel.isempty)
        {
            this.Hide();
        }
        else
        {
            this.Show();
        }

        if (this.Element != this.DataModel.element)
        {
            this.SetElement(this.DataModel.element);
        }
        
        if(this.ShowFrame != this.DataModel.bshowframe)
		{
        	this.SetFrame(this.DataModel.bshowframe);
        } 
        
    }

    SetElement(NewElement)
    {
        this.UpdateElement(NewElement.toLowerCase())
        this.Element = NewElement.toLowerCase();
    }

    Refresh()
    {
        let NewElement = this.parentElement.hasAttribute("oak-element") ? this.parentElement.getAttribute("oak-element") : "";
        if(NewElement == "" || NewElement === "noelement")
        {
            this.Hide();
        }
        else
        {
            this.UpdateElement(NewElement);
        }

        this.Element = NewElement.toLowerCase();
    }

    UpdateElement(NewElement)
    {
        let DamageTypeIcon = this.querySelector(".damagetype_icon");

        let OldTint = "tint-"+this.Element;
        let NewTint = "tint-"+NewElement;

        DamageTypeIcon.classList.remove(OldTint);
        DamageTypeIcon.classList.remove(this.Element);
        DamageTypeIcon.classList.add(NewTint);
        DamageTypeIcon.classList.add(NewElement);
    }
    
    SetFrame(NewFrameVisibility)
    {
        let IconFrame = this.querySelector(".damagetype_frame");
        
        if(NewFrameVisibility)
		{
			IconFrame.classList.add("frame");   
        }
        else
        {
            IconFrame.classList.remove("frame");
        }
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
window.customElements.define('elemental-damagetype', OakElementDamageType);
