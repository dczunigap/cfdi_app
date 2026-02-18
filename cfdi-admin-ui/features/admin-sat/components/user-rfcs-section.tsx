import { Trash2 } from "lucide-react";

import type { AdminUser, RegimenFiscalCatalog, TipoPersonaCatalog, UserRfc } from "../types";

type UserRfcsSectionProps = {
  users: AdminUser[];
  tiposPersona: TipoPersonaCatalog[];
  regimenesForTipoPersona: RegimenFiscalCatalog[];
  userRfcs: UserRfc[];
  selectedUserId: number | null;
  userTipoPersonaClave: "PM" | "PF" | "EXT" | "";
  userRegimenFiscalClave: string;
  userRfc: string;
  userRfcError: string | null;
  isCatalogsLoading: boolean;
  isAddPending: boolean;
  isDeletePending: boolean;
  isUserRfcsLoading: boolean;
  onUserChange: (value: string) => void;
  onUserTipoPersonaChange: (value: "PM" | "PF" | "EXT" | "") => void;
  onUserRegimenFiscalChange: (value: string) => void;
  onUserRfcChange: (value: string) => void;
  onAddUserRfc: () => void;
  onRemoveUserRfc: (rfc: string) => void;
};

export default function UserRfcsSection(props: UserRfcsSectionProps) {
  const {
    users,
    tiposPersona,
    regimenesForTipoPersona,
    userRfcs,
    selectedUserId,
    userTipoPersonaClave,
    userRegimenFiscalClave,
    userRfc,
    userRfcError,
    isCatalogsLoading,
    isAddPending,
    isDeletePending,
    isUserRfcsLoading,
    onUserChange,
    onUserTipoPersonaChange,
    onUserRegimenFiscalChange,
    onUserRfcChange,
    onAddUserRfc,
    onRemoveUserRfc,
  } = props;

  return (
    <>
      <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
        <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
          Usuarios
        </div>
        <h3 className="mt-2 text-lg font-semibold text-white">
          RFCs permitidos por usuario
        </h3>
        <p className="text-sm text-slate-400">
          Asocia RFCs a usuarios para habilitar descargas SAT.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-5">
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Usuario
            <select
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              onChange={(event) => onUserChange(event.target.value)}
              value={selectedUserId ?? ""}
            >
              <option value="">Selecciona un usuario</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.username ?? "sin-username"} · {user.email ?? "-"}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Tipo de persona
            <select
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              onChange={(event) =>
                onUserTipoPersonaChange(event.target.value as "PM" | "PF" | "EXT" | "")
              }
              value={userTipoPersonaClave}
              disabled={isCatalogsLoading}
            >
              <option value="">Selecciona tipo</option>
              {tiposPersona.map((row) => (
                <option key={row.clave} value={row.clave}>
                  {row.clave} - {row.descripcion}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Regimen fiscal
            <select
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              onChange={(event) => onUserRegimenFiscalChange(event.target.value)}
              value={userRegimenFiscalClave}
              disabled={isCatalogsLoading || !userTipoPersonaClave}
            >
              <option value="">Selecciona regimen</option>
              {regimenesForTipoPersona.map((row) => (
                <option key={`${row.tipo_persona_clave}-${row.clave}`} value={row.clave}>
                  {row.clave} - {row.descripcion}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            RFC
            <input
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              value={userRfc}
              onChange={(event) => onUserRfcChange(event.target.value.toUpperCase())}
              placeholder="AAA010101AAA"
            />
          </label>
          <div className="flex items-end">
            <button
              className="w-full rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-sky-500/30 transition hover:shadow-md"
              type="button"
              onClick={onAddUserRfc}
              disabled={isAddPending}
            >
              {isAddPending ? "Guardando..." : "Agregar RFC"}
            </button>
          </div>
        </div>
        {userRfcError ? <p className="mt-3 text-sm text-rose-400">{userRfcError}</p> : null}
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 shadow-sm">
        <div className="border-b border-white/10 px-5 py-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Usuarios
          </div>
          <h3 className="mt-2 text-lg font-semibold text-white">RFCs asociados</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950 text-xs uppercase tracking-[0.18em] text-slate-400">
              <tr>
                <th className="px-5 py-3">RFC</th>
                <th className="px-5 py-3">Tipo</th>
                <th className="px-5 py-3">Regimen</th>
                <th className="px-5 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {userRfcs.map((row) => (
                <tr key={`${row.user_id}:${row.rfc}`}>
                  <td className="px-5 py-4 font-medium text-white">{row.rfc}</td>
                  <td className="px-5 py-4 text-slate-300">{row.tipo_persona_clave}</td>
                  <td className="px-5 py-4 text-slate-300">
                    {row.regimen_fiscal_clave} - {row.regimen_fiscal_descripcion}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <button
                      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-rose-500/30 text-rose-300 transition hover:border-rose-500/60 hover:text-rose-200"
                      onClick={() => onRemoveUserRfc(row.rfc)}
                      disabled={isDeletePending}
                      aria-label="Eliminar RFC"
                      title="Eliminar"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              ))}
              {!selectedUserId ? (
                <tr>
                  <td className="px-5 py-6 text-center text-slate-400" colSpan={4}>
                    Selecciona un usuario para ver sus RFCs.
                  </td>
                </tr>
              ) : null}
              {selectedUserId && userRfcs.length === 0 && !isUserRfcsLoading ? (
                <tr>
                  <td className="px-5 py-6 text-center text-slate-400" colSpan={4}>
                    Este usuario no tiene RFCs asociados.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
