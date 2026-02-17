import { apiFetch } from "@/lib/api";
import type {
  DeclaracionConfigCatalogs,
  DeclaracionConfigGet,
  DeclaracionConfigUpsertPayload,
  DeclaracionConfigUpsertResponse,
  TipoDeclaracionClave,
} from "./types";

export async function listDeclaracionConfigCatalogs(): Promise<DeclaracionConfigCatalogs> {
  return apiFetch<DeclaracionConfigCatalogs>("/admin/declaracion-config/catalogos");
}

export async function getDeclaracionConfig(
  regimenFiscalClave: string,
  tipoDeclaracion: TipoDeclaracionClave
): Promise<DeclaracionConfigGet> {
  const params = new URLSearchParams({
    regimen_fiscal_clave: regimenFiscalClave,
    tipo_declaracion: tipoDeclaracion,
  });
  return apiFetch<DeclaracionConfigGet>(`/admin/declaracion-config?${params.toString()}`);
}

export async function upsertDeclaracionConfig(
  payload: DeclaracionConfigUpsertPayload
): Promise<DeclaracionConfigUpsertResponse> {
  return apiFetch<DeclaracionConfigUpsertResponse>("/admin/declaracion-config", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
