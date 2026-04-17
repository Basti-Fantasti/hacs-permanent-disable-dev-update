import { describe, it, expect } from "vitest";
import { fixture, html as tplHtml } from "@open-wc/testing-helpers";
import "./settings-view";
import type { SettingsView } from "./settings-view";

describe("<settings-view>", () => {
  it("displays current options", async () => {
    const opts = {
      scan_start_time: "02:15",
      scan_max_duration_minutes: 45,
      per_device_timeout_seconds: 120,
    };
    const el = await fixture<SettingsView>(
      tplHtml`<settings-view .options=${opts}></settings-view>`,
    );
    expect(el.shadowRoot!.textContent).toMatch(/02:15/);
    expect(el.shadowRoot!.textContent).toMatch(/45/);
    expect(el.shadowRoot!.textContent).toMatch(/120/);
  });
});
