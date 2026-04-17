const BASE = "/api/update_blocklist";

export interface Block {
  id: string;
  device_id: string;
  update_entity_ids: string[];
  unique_ids: string[];
  fingerprint: { manufacturer: string; model: string; name: string };
  reason: string;
  created_at: string;
  last_known_version: string | null;
  last_scan_at: string | null;
  last_scan_status: string;
  status: string;
}

export interface Candidate {
  device_id: string;
  name: string;
  manufacturer: string | null;
  model: string | null;
  update_entity_ids: string[];
}

export interface Options {
  scan_start_time: string;
  scan_max_duration_minutes: number;
  per_device_timeout_seconds: number;
}

export interface PendingRediscovery {
  orphan_block_id: string;
  candidate_device_id: string;
  match_type: "unique_id" | "fingerprint";
  detected_at: string;
}

export interface BlocksResponse {
  blocks: Block[];
  pending_rediscovery: PendingRediscovery[];
}

export class BlocklistApi {
  constructor(private token: string) {}

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const resp = await fetch(path, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
        ...(init.headers ?? {}),
      },
    });
    if (!resp.ok) {
      const body = typeof (resp as any).text === "function" ? await (resp as any).text() : "";
      throw new Error(`${resp.status} ${body}`);
    }
    if (resp.status === 204) return undefined as T;
    return (await resp.json()) as T;
  }

  listBlocks(): Promise<BlocksResponse> {
    return this.request<BlocksResponse>(`${BASE}/blocks`);
  }

  addBlock(deviceId: string, reason: string): Promise<Block> {
    return this.request<Block>(`${BASE}/blocks`, {
      method: "POST",
      body: JSON.stringify({ device_id: deviceId, reason }),
    });
  }

  removeBlock(blockId: string): Promise<void> {
    return this.request<void>(`${BASE}/blocks/${encodeURIComponent(blockId)}`, {
      method: "DELETE",
    });
  }

  listCandidates(): Promise<{ candidates: Candidate[] }> {
    return this.request(`${BASE}/candidates`);
  }

  getOptions(): Promise<Options> {
    return this.request<Options>(`${BASE}/options`);
  }

  scan(blockId?: string): Promise<void> {
    return this.request<void>(`${BASE}/scan`, {
      method: "POST",
      body: JSON.stringify(blockId ? { block_id: blockId } : {}),
    });
  }

  resolveRediscovery(
    orphanBlockId: string,
    action: "accept" | "decline" | "dismiss",
    candidateDeviceId?: string,
  ): Promise<void> {
    return this.request<void>(`${BASE}/rediscovery/resolve`, {
      method: "POST",
      body: JSON.stringify({
        orphan_block_id: orphanBlockId,
        candidate_device_id: candidateDeviceId ?? null,
        action,
      }),
    });
  }
}
