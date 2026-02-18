import { CheckCircle2, Trash2, XCircle } from "lucide-react";

import type { SatCredential } from "../types";

type UploadMode = "pfx" | "cerkey";

type CredentialsSectionProps = {
  mode: UploadMode;
  rfc: string;
  keyPassword: string;
  credentialsError: string | null;
  credentials: SatCredential[];
  isLoadingCredentials: boolean;
  isSavingCredentials: boolean;
  isDeletingCredentials: boolean;
  onSetMode: (mode: UploadMode) => void;
  onSetRfc: (value: string) => void;
  onSetKeyPassword: (value: string) => void;
  onFileChange: (
    event: React.ChangeEvent<HTMLInputElement>,
    kind: "pfx" | "cert" | "key"
  ) => void;
  onSaveCredentials: () => void;
  onDeleteCredential: (rfc: string) => void;
};

export default function CredentialsSection(props: CredentialsSectionProps) {
  const {
    mode,
    rfc,
    keyPassword,
    credentialsError,
    credentials,
    isLoadingCredentials,
    isSavingCredentials,
    isDeletingCredentials,
    onSetMode,
    onSetRfc,
    onSetKeyPassword,
    onFileChange,
    onSaveCredentials,
    onDeleteCredential,
  } = props;

  return (
    <>
      <div
        id="credentials"
        className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm"
      >
        <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
          Credenciales
        </div>
        <h2 className="mt-2 text-lg font-medium text-white">
          Subir credenciales
        </h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            RFC
            <input
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              value={rfc}
              onChange={(event) => onSetRfc(event.target.value.toUpperCase())}
              placeholder="RFC"
              autoComplete="off"
            />
          </label>
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Password
            <input
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              value={keyPassword}
              onChange={(event) => onSetKeyPassword(event.target.value)}
              placeholder="Password"
              type="password"
              autoComplete="new-password"
            />
          </label>
        </div>

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            className={`w-28 rounded-full border px-4 py-2 text-sm transition ${
              mode === "pfx"
                ? "border-sky-500 bg-sky-500/20 text-white"
                : "border-white/10 bg-slate-950 text-slate-300 hover:bg-white/5"
            }`}
            onClick={() => onSetMode("pfx")}
          >
            PFX
          </button>
          <button
            type="button"
            className={`w-28 rounded-full border px-4 py-2 text-sm transition ${
              mode === "cerkey"
                ? "border-sky-500 bg-sky-500/20 text-white"
                : "border-white/10 bg-slate-950 text-slate-300 hover:bg-white/5"
            }`}
            onClick={() => onSetMode("cerkey")}
          >
            CER / KEY
          </button>
        </div>

        {mode === "pfx" ? (
          <div className="mt-4">
            <label className="text-sm text-slate-300">
              Archivo .pfx
              <input
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white file:mr-3 file:rounded-full file:border-0 file:bg-sky-500/20 file:px-3 file:py-1 file:text-sky-200"
                type="file"
                accept=".pfx"
                onChange={(event) => onFileChange(event, "pfx")}
              />
            </label>
          </div>
        ) : null}

        {mode === "cerkey" ? (
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="text-sm text-slate-300">
              Archivo .cer
              <input
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white file:mr-3 file:rounded-full file:border-0 file:bg-sky-500/20 file:px-3 file:py-1 file:text-sky-200"
                type="file"
                accept=".cer"
                onChange={(event) => onFileChange(event, "cert")}
              />
            </label>
            <label className="text-sm text-slate-300">
              Archivo .key
              <input
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white file:mr-3 file:rounded-full file:border-0 file:bg-sky-500/20 file:px-3 file:py-1 file:text-sky-200"
                type="file"
                accept=".key"
                onChange={(event) => onFileChange(event, "key")}
              />
            </label>
          </div>
        ) : null}

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            className="w-full rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-sky-500/30 transition hover:shadow-md md:w-auto"
            disabled={isSavingCredentials}
            onClick={onSaveCredentials}
          >
            {isSavingCredentials ? "Guardando..." : "Guardar credenciales"}
          </button>
          {credentialsError ? (
            <span className="text-sm text-rose-400">{credentialsError}</span>
          ) : null}
        </div>
      </div>

      <div
        id="rfc-users"
        className="rounded-2xl border border-white/10 bg-white/5 shadow-sm"
      >
        <div className="border-b border-white/10 px-5 py-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Credenciales
          </div>
          <h3 className="mt-2 text-lg font-semibold text-white">
            Credenciales en BD
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950 text-xs uppercase tracking-[0.18em] text-slate-400">
              <tr>
                <th className="px-5 py-3">RFC</th>
                <th className="px-5 py-3">Creado</th>
                <th className="px-5 py-3">Actualizado</th>
                <th className="px-5 py-3">PFX</th>
                <th className="px-5 py-3">Password</th>
                <th className="px-5 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {credentials.map((row) => (
                <tr key={row.rfc}>
                  <td className="px-5 py-4 font-medium text-white">
                    {row.rfc}
                  </td>
                  <td className="px-5 py-4 text-slate-400">{row.created_at}</td>
                  <td className="px-5 py-4 text-slate-400">
                    {row.updated_at ?? "-"}
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex h-7 w-7 items-center justify-center rounded-full ${
                        row.has_pfx ? "bg-emerald-500/20" : "bg-rose-500/20"
                      }`}
                    >
                      {row.has_pfx ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-300" />
                      ) : (
                        <XCircle className="h-4 w-4 text-rose-300" />
                      )}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex h-7 w-7 items-center justify-center rounded-full ${
                        row.has_password ? "bg-emerald-500/20" : "bg-rose-500/20"
                      }`}
                    >
                      {row.has_password ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-300" />
                      ) : (
                        <XCircle className="h-4 w-4 text-rose-300" />
                      )}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <button
                      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-rose-500/30 text-rose-300 transition hover:border-rose-500/60 hover:text-rose-200"
                      disabled={isDeletingCredentials}
                      onClick={() => onDeleteCredential(row.rfc)}
                      aria-label="Eliminar credenciales"
                      title="Eliminar"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              ))}
              {!isLoadingCredentials && credentials.length === 0 ? (
                <tr>
                  <td className="px-5 py-6 text-center text-slate-400" colSpan={6}>
                    Sin credenciales registradas.
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
