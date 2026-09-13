"use strict";

class MarkupManager
{
    constructor()
    {
        this.SpecialMarkupMap = new Map();
        this.MarkupStartCharacter = '[';
        this.MarkupEndCharacter = ']';

        this.EndSpanCheckLength = 7;
        this.EndSpanCheckLengthWithNBSP = 13;

        this.SpecialMarkupMap.set("newline", { requiresEndSection: false, special_text: "</p><p cohinline class=\"markup_newline markup_content\">" });

        this.SpecialMarkupMap.set("steam", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("switch", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("epic", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("psn", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("xboxlive", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("shift", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("cash", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("gold_key", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("eridium", { requiresEndSection: false, isImageIcon: true });

        this.SpecialMarkupMap.set("corrosive_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("cryo_icon", { requiresEndSection: false, isImageIcon: true });
		this.SpecialMarkupMap.set("fire_icon", { requiresEndSection: false, isImageIcon: true });
		this.SpecialMarkupMap.set("incendiary_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("kinetic_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("radiation_icon", { requiresEndSection: false, isImageIcon: true });
		this.SpecialMarkupMap.set("shock_icon", { requiresEndSection: false, isImageIcon: true });
		this.SpecialMarkupMap.set("electric_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("elemental_icon", { requiresEndSection: false, isImageIcon: true });

        this.SpecialMarkupMap.set("siren_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("gravitar_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("exo_icon", { requiresEndSection: false, isImageIcon: true });
		this.SpecialMarkupMap.set("paladin_icon", { requiresEndSection: false, isImageIcon: true });

		this.SpecialMarkupMap.set("recent_party_leader_icon", { requiresEndSection: false, isImageIcon: true });

        this.SpecialMarkupMap.set("maliwan_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("atlas_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("jakobs_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("cov_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("daedalus_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("hyperion_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("order_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("borg_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("tediore_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("torgue_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("vladof_icon", { requiresEndSection: false, isImageIcon: true });

        this.SpecialMarkupMap.set("cs_avail_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("cs_unav_icon", { requiresEndSection: false, isImageIcon: true });

        this.SpecialMarkupMap.set("dlc_warning", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("warning", { requiresEndSection: false, isImageIcon: true });

        this.SpecialMarkupMap.set("wfll_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("frtn_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("roll_icon", { requiresEndSection: false, isImageIcon: true });

        this.SpecialMarkupMap.set("func_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("exe_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("symb_icon", { requiresEndSection: false, isImageIcon: true });

        this.SpecialMarkupMap.set("fasttravel_icon", { requiresEndSection: false, isImageIcon: true });
        this.SpecialMarkupMap.set("sdu_icon", { requiresEndSection: false, isImageIcon: true });
    }

    Init()
    {

    }

    ResolveMarkupText(originalText, options)
    {
		options = options || {};
        if (originalText === undefined)
        {
            return originalText;
        }

        if (originalText === null)
        {
            return originalText;
        }

        // Don't try to look for markup if not a string.
        if (!(typeof originalText === 'string' || originalText instanceof String))
        {
            return originalText;
        }

		let startSearchingOffset = 0;
        let beginningBookendStart = originalText.indexOf(this.MarkupStartCharacter, startSearchingOffset);

        let keepSearching = true;

        if (beginningBookendStart != -1)
        {
            let outResult = originalText;
            while (keepSearching)
            {
                keepSearching = false;
                
                let beginningBookendEnd = outResult.indexOf(this.MarkupEndCharacter, beginningBookendStart + 1);
                
                if ((beginningBookendStart >= 0) && beginningBookendEnd > beginningBookendStart)
                {
                    let requiresEndSection = true;
                    let markupInfo = undefined;
                    let markupKey = outResult.substring(beginningBookendStart + this.MarkupStartCharacter.length, beginningBookendEnd - this.MarkupEndCharacter.length + 1);
                    
                    if (this.SpecialMarkupMap.has(markupKey))
                    {
                        markupInfo = this.SpecialMarkupMap.get(markupKey);
                        if (markupInfo.requiresEndSection !== undefined)
                        {
                            requiresEndSection = markupInfo.requiresEndSection;
                        }
                    }
    
                    if (requiresEndSection)
                    {
                        let endingBookend = outResult.indexOf(this.MarkupStartCharacter + "/" + markupKey + this.MarkupEndCharacter);
                        if (endingBookend > beginningBookendEnd)
                        {
                            keepSearching = true;
                            let payloadToMarkup = outResult.substring(beginningBookendEnd + this.MarkupStartCharacter.length, endingBookend - this.MarkupEndCharacter.length + 1);
    
                            if (payloadToMarkup.length <= 0)
                            {
                                console.warn("[MarkupManager] payloadToMarkup is empty. args: originalText:", originalText, "options:", JSON.stringify(options));
                            }
                            
                            let leftOutput = outResult.substring(0, beginningBookendStart);
                            let rightOutput = outResult.substring(endingBookend + this.MarkupStartCharacter.length + markupKey.length + this.MarkupEndCharacter.length + 1);

                            let finalMarkup = "";
                            let needNBSPCorrectedString = true;
                            let isGlyphMarkup = false;
                            let needGlyphCorrectedLeftString = false;

                            // If we're inside of another span, the exterior span should have handled the nbsp.
                            let canDoEndSpanCheck = rightOutput.length >= this.EndSpanCheckLength;
                            if (canDoEndSpanCheck)
                            {
                                let endSpanCheck = rightOutput.substring(0, this.EndSpanCheckLength);
                                if (endSpanCheck === "</span>")
                                {
                                    needNBSPCorrectedString = false;
                                }
                                else
                                {
                                    let specialEndSpanCheck = rightOutput.substring(0, this.EndSpanCheckLengthWithNBSP);
                                    if (specialEndSpanCheck === "&nbsp;</span>")
                                    {
                                        needNBSPCorrectedString = false;
                                    }
                                }
                            }

                            if (needNBSPCorrectedString)
                            {
                                if (this.IsSpecialCaseSubstring(rightOutput))
                                {
                                    needNBSPCorrectedString = false;
                                }
                            }

                            if (LanguageSettings.DisableNBSPMarkup)
                            {
                                needNBSPCorrectedString = false;
                            }

                            if (markupKey === "glyph")
                            {
                                isGlyphMarkup = true;
                                needGlyphCorrectedLeftString = this.NeedGlyphCorrectedLeftString(leftOutput);
                                let needGlyphRightNBSP = this.NeedGlyphRightNBSP(rightOutput);
                                finalMarkup = this.GetGlyphMarkupString(payloadToMarkup, options.attributes, needGlyphCorrectedLeftString, needGlyphRightNBSP);
                            }
                            else if (markupKey === "key")
                            {
                                isGlyphMarkup = true;
                                needGlyphCorrectedLeftString = this.NeedGlyphCorrectedLeftString(leftOutput);
                                let needGlyphRightNBSP = this.NeedGlyphRightNBSP(rightOutput);
                                finalMarkup = this.GetKeyMarkupString(payloadToMarkup, options.attributes, needGlyphCorrectedLeftString, needGlyphRightNBSP);
                            }
                            else if (markupKey === "gamepad_key")
                            {
                                isGlyphMarkup = true;
                                needGlyphCorrectedLeftString = this.NeedGlyphCorrectedLeftString(leftOutput);
                                let needGlyphRightNBSP = this.NeedGlyphRightNBSP(rightOutput);
                                finalMarkup = this.GetGamepadKeyMarkupString(payloadToMarkup, options.attributes, needGlyphCorrectedLeftString, needGlyphRightNBSP);
                            }
                            else if (markupKey === "nowrap")
                            {
                                finalMarkup = this.GetPayloadMarkupSpan(markupKey, payloadToMarkup, needNBSPCorrectedString);
                            }
                            else if (markupKey === "glyph_special")
                            {
                                isGlyphMarkup = true;
                                needGlyphCorrectedLeftString = this.NeedGlyphCorrectedLeftString(leftOutput);
                                let needGlyphRightNBSP = this.NeedGlyphRightNBSP(rightOutput);
                                finalMarkup = this.GetGlyphMarkupString(payloadToMarkup, [], needGlyphCorrectedLeftString, needGlyphRightNBSP);
                            }
                            else
                            {
                                finalMarkup = this.GetPayloadMarkupSpan(markupKey, payloadToMarkup, needNBSPCorrectedString);
                            }
                            
                            if (needGlyphCorrectedLeftString)
                            {
                                leftOutput = this.GetGlyphCorrectedLeftString(leftOutput);
                            }

                            if (needNBSPCorrectedString)
                            {
                                rightOutput = this.GetNBSPCorrectedString(rightOutput);
                            }

                            let rightOutputFirstChar = rightOutput.charAt(0);

                            if (!isGlyphMarkup && this.IsPunctuation(rightOutputFirstChar)) 
                            {
                                finalMarkup = this.GetPayloadMarkupSpan(markupKey, payloadToMarkup, false) + rightOutputFirstChar + ' ';
                                rightOutput = this.GetNBSPCorrectedString(rightOutput.substring(1));
                            }
    
                            outResult = leftOutput + finalMarkup + rightOutput;
                        }
                        else if (endingBookend === -1)
                        {
                            // We found something that wasn't intended as markup, skip this section and search the part of the string afterwards.
                            keepSearching = true;
                            startSearchingOffset = beginningBookendEnd + 1;
                        }
                    }
                    else if (markupInfo !== undefined)
                    {
                        keepSearching = true;
                        if (markupInfo.isImageIcon !== undefined && markupInfo.isImageIcon)
                        {
                            let finalMarkup = '<span class="oak-markup img_icon ' + markupKey + '">&nbsp;</span>';
                            let leftOutput = outResult.substring(0, beginningBookendStart);
                            let rightOutput = this.GetNBSPCorrectedString(outResult.substring(beginningBookendEnd + 1));
                            outResult = leftOutput + finalMarkup + rightOutput;
                        }
                        else if (markupInfo.special_text !== undefined)
                        {
                            let leftOutput = outResult.substring(0, beginningBookendStart);
                            let rightOutput = outResult.substring(beginningBookendEnd + 1);
                            outResult = leftOutput + markupInfo.special_text + rightOutput;
                        }
                        else
                        {
                            keepSearching = false;
                        }
                    }
                    else
                    {
                        keepSearching = false;
                    }
                }
                else if (beginningBookendStart >= 0)
                {
                    keepSearching = true;
                    startSearchingOffset = beginningBookendStart + 1;
                }

                beginningBookendStart = outResult.indexOf(this.MarkupStartCharacter, startSearchingOffset);
            }
            outResult = `<p cohinline class="markup_content">${outResult}</p>`;

            return outResult;
        }

        return originalText;
    }

    GetNBSPCorrectedString(inputString)
    {
        if (inputString.indexOf(' ') === 0)
        {
            inputString = `${inputString.substring(1)}`;
        }

        return inputString;
    }

    NeedGlyphCorrectedLeftString(inputString)
    {
        let lastChar = inputString.charAt(inputString.length - 1);
        return lastChar === ' ' && !LanguageSettings.DisableNBSPMarkup;
    }

    NeedGlyphRightNBSP(inputString)
    {
        // TODO OAK2-173433 - Remove this once the typo in Tooltip_DarkSiren_ActionSkill_PhaseShard_Capstone_GrimReaper gets fixed.
        // I love it when I have to do the obviously wrong thing because someone messed up text formatting somewhere and nobody noticed until
        // after localization got locked.
        return !LanguageSettings.DisableNBSPMarkup;

        // TODO OAK2-173433 - Uncomment this section once the typo in Tooltip_DarkSiren_ActionSkill_PhaseShard_Capstone_GrimReaper gets fixed.
        /*
        let firstChar = inputString.charAt(0);
        return firstChar === ' ';
        */
    }

    GetGlyphCorrectedLeftString(inputString)
    {
        return `${inputString.substring(0, inputString.length - 1)}`;
    }

	GetGlyphMarkup(glyphMarkupContents, attributes) {
		const glyphElem = document.createElement("gbx-glyph");
		
		// Only keep valid markup options
		attributes = attributes?.filter(validAttribute => [...glyphElem.constructor.observedAttributes].includes(validAttribute.name)) || [];
		glyphElem.classList.add("Ico_Glyph_Markup");
		attributes.forEach((attribute) => {
			glyphElem.setAttribute(attribute.name, attribute.value);
		});
		return glyphElem;
	}

    GetFinalGlyphMarkupString(glyphMarkupElement, needGlyphLeftNBSP, needGlyphRightNBSP)
    {
        if (!glyphMarkupElement)
        {
            return "";
        }

        let glyphHTML = glyphMarkupElement.outerHTML;
        let glyphLeftNBSP = needGlyphLeftNBSP ? "&nbsp;" : "";
        let glyphRightNBSP = needGlyphRightNBSP ? "&nbsp;" : "";

        return `<span class="oak-markup nowrap">${glyphLeftNBSP}${glyphHTML}${glyphRightNBSP}</span>`;
    }
    
	GetGlyphMarkupString(glyphMarkupContents, attributes, needGlyphLeftNBSP, needGlyphRightNBSP) {
		attributes = attributes || [];
		const defaultAttributes = [{name: "action", value: glyphMarkupContents}, {name: "submap", value: ""}];
		attributes = [...defaultAttributes, ...attributes];
        let glyphMarkupElement = this.GetGlyphMarkup(glyphMarkupContents, attributes);

        return this.GetFinalGlyphMarkupString(glyphMarkupElement, needGlyphLeftNBSP, needGlyphRightNBSP);
	}

    GetKeyMarkupString(glyphMarkupContents, attributes, needGlyphLeftNBSP, needGlyphRightNBSP)
    {
		attributes = attributes || [];
		const defaultAttributes = [{name: "key", value: glyphMarkupContents}, {name: "submap", value: ""}, {name:"force_keyboard", value:"true"}];
		attributes = [...defaultAttributes, ...attributes];
		let glyphMarkupElement = this.GetGlyphMarkup(glyphMarkupContents, attributes);

        return this.GetFinalGlyphMarkupString(glyphMarkupElement, needGlyphLeftNBSP, needGlyphRightNBSP);
    }

    GetGamepadKeyMarkupString(glyphMarkupContents, attributes, needGlyphLeftNBSP, needGlyphRightNBSP)
    {
		attributes = attributes || [];
		const defaultAttributes = [{name: "key", value: glyphMarkupContents}, {name: "submap", value: ""}, {name:"force_gamepad", value:"true"}];
		attributes = [...defaultAttributes, ...attributes];
		let glyphMarkupElement = this.GetGlyphMarkup(glyphMarkupContents, attributes);
        
        return this.GetFinalGlyphMarkupString(glyphMarkupElement, needGlyphLeftNBSP, needGlyphRightNBSP);
    }

    IsPunctuation(targetCharacter)
    {
        return targetCharacter === '.' || targetCharacter === ',';
    }

    IsSpecialCaseSubstring(targetSubstring)
    {
        // Addressing OAK2-165838
        return (targetSubstring.charAt(0) === '-' && targetSubstring.charAt(1) !== ' ') || (targetSubstring.charAt(0) === ')');
    }

    GetPayloadMarkupSpan(markupKey, payloadToMarkup, nbsp = true) 
    {
        if (nbsp) 
        {
            return `<span class="oak-markup ${markupKey}">${payloadToMarkup}&nbsp;</span>`;
        }
        return `<span class="oak-markup ${markupKey}">${payloadToMarkup}</span>`;
    }
}