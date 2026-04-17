import { describe, it, expect, beforeEach, vi } from "vitest";
import { BlocklistApi } from "./api-client";

describe("BlocklistApi", () => {
  beforeEach(() => {
    (global as any).fetch = vi.fn();
  });

  it("listBlocks calls the list endpoint", async () => {
    (global as any).fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ blocks: [], pending_rediscovery: [] }),
    });

    const api = new BlocklistApi("TOKEN");
    const data = await api.listBlocks();
    expect(data).toEqual({ blocks: [], pending_rediscovery: [] });
    expect((global as any).fetch).toHaveBeenCalledWith(
      "/api/update_blocklist/blocks",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer TOKEN" }),
      }),
    );
  });

  it("addBlock posts to the blocks endpoint", async () => {
    (global as any).fetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => ({ id: "b1" }),
    });

    const api = new BlocklistApi("T");
    const block = await api.addBlock("dev1", "reason");
    expect(block.id).toBe("b1");
    expect((global as any).fetch).toHaveBeenCalledWith(
      "/api/update_blocklist/blocks",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ device_id: "dev1", reason: "reason" }),
      }),
    );
  });

  it("removeBlock deletes the block", async () => {
    (global as any).fetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
    });

    const api = new BlocklistApi("T");
    await api.removeBlock("b1");
    expect((global as any).fetch).toHaveBeenCalledWith(
      "/api/update_blocklist/blocks/b1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("listBlocks throws on non-2xx", async () => {
    (global as any).fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => "boom",
    });

    const api = new BlocklistApi("T");
    await expect(api.listBlocks()).rejects.toThrow(/500/);
  });
});
