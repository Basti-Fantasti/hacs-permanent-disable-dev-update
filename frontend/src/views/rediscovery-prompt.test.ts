import { describe, it, expect } from "vitest";
import { fixture, html as tplHtml } from "@open-wc/testing-helpers";
import "./rediscovery-prompt";
import type { RediscoveryPrompt } from "./rediscovery-prompt";

describe("<rediscovery-prompt>", () => {
  it("renders nothing when no pending items", async () => {
    const el = await fixture<RediscoveryPrompt>(
      tplHtml`<rediscovery-prompt .pending=${[]}></rediscovery-prompt>`,
    );
    // shadowRoot.textContent includes the <style> block in jsdom; verify no .item divs rendered
    expect(el.shadowRoot!.querySelectorAll(".item").length).toBe(0);
  });

  it("emits resolve event with action and ids", async () => {
    const pending = [
      {
        orphan_block_id: "b1",
        candidate_device_id: "newdev",
        match_type: "unique_id" as const,
        detected_at: "now",
      },
    ];
    const el = await fixture<RediscoveryPrompt>(
      tplHtml`<rediscovery-prompt .pending=${pending}></rediscovery-prompt>`,
    );
    const events: CustomEvent[] = [];
    el.addEventListener("resolve", (e) => events.push(e as CustomEvent));

    (el.shadowRoot!.querySelector("[data-action='accept']") as HTMLButtonElement).click();
    expect(events[0].detail).toEqual({
      orphan_block_id: "b1",
      candidate_device_id: "newdev",
      action: "accept",
    });
  });
});
