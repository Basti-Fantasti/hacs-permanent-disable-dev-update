import { describe, it, expect } from "vitest";
import { fixture, html as tplHtml } from "@open-wc/testing-helpers";
import "./add-block-dialog";
import type { AddBlockDialog } from "./add-block-dialog";
import type { Candidate } from "../api-client";

const candidate: Candidate = {
  device_id: "d1",
  name: "Test Device",
  manufacturer: "Espressif",
  model: "ESP",
  update_entity_ids: ["update.a"],
};

describe("<add-block-dialog>", () => {
  it("renders candidates as options", async () => {
    const el = await fixture<AddBlockDialog>(
      tplHtml`<add-block-dialog .candidates=${[candidate]}></add-block-dialog>`,
    );
    const options = el.shadowRoot!.querySelectorAll("option");
    expect(options.length).toBe(2); // placeholder + one candidate
    expect(options[1].textContent).toMatch(/Test Device/);
  });

  it("dispatches block-add event with form values", async () => {
    const el = await fixture<AddBlockDialog>(
      tplHtml`<add-block-dialog .candidates=${[candidate]}></add-block-dialog>`,
    );
    const select = el.shadowRoot!.querySelector("select") as HTMLSelectElement;
    const textarea = el.shadowRoot!.querySelector("textarea") as HTMLTextAreaElement;
    select.value = "d1";
    select.dispatchEvent(new Event("change"));
    await el.updateComplete;
    textarea.value = "because reasons";
    textarea.dispatchEvent(new Event("input"));
    await el.updateComplete;

    const events: CustomEvent[] = [];
    el.addEventListener("block-add", (e) => events.push(e as CustomEvent));
    (el.shadowRoot!.querySelector("button[type='submit']") as HTMLButtonElement).click();

    expect(events.length).toBe(1);
    expect(events[0].detail).toEqual({ device_id: "d1", reason: "because reasons" });
  });
});
