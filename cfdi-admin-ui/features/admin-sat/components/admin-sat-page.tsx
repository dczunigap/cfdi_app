"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  Pencil,
  Save,
  Trash2,
  X,
  XCircle,
} from "lucide-react";

import {
  addUserRfc,
  deleteRfcPhone,
  deleteSatCredentials,
  deleteUserRfc,
  listAdminUsers,
  listRfcPhones,
  listSatCredentials,
  listUserRfcCatalogs,
  listUserRfcs,
  upsertRfcPhone,
  upsertSatCredentials,
} from "../api";
import type { RegimenFiscalCatalog, RfcPhone } from "../types";
import { getErrorMessage } from "@/lib/errors";

type UploadMode = "pfx" | "cerkey";

const RFC_REGEX = /^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$/;
const PHONE_REGEX = /^\d{8,15}$/;

export default function AdminSatPage() {
  const queryClient = useQueryClient();

  const [mode, setMode] = useState<UploadMode>("pfx");
  const [rfc, setRfc] = useState("");
  const [keyPassword, setKeyPassword] = useState("");
  const [pfxFile, setPfxFile] = useState<File | null>(null);
  const [certFile, setCertFile] = useState<File | null>(null);
  const [keyFile, setKeyFile] = useState<File | null>(null);
  const [credentialsError, setCredentialsError] = useState<string | null>(null);

  const [phone, setPhone] = useState("");
  const [phoneRfc, setPhoneRfc] = useState("");
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [showPhoneForm, setShowPhoneForm] = useState(false);
  const [editingPhoneId, setEditingPhoneId] = useState<number | null>(null);
  const [editingPhone, setEditingPhone] = useState("");
  const [editingRfc, setEditingRfc] = useState("");

  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [userTipoPersonaClave, setUserTipoPersonaClave] = useState<
    "PM" | "PF" | "EXT" | ""
  >("");
  const [userRfc, setUserRfc] = useState("");
  const [userRegimenFiscalClave, setUserRegimenFiscalClave] = useState("");
  const [userRfcError, setUserRfcError] = useState<string | null>(null);

  const credentialsQuery = useQuery({
    queryKey: ["sat-credentials"],
    queryFn: listSatCredentials,
  });

  const phonesQuery = useQuery({
    queryKey: ["rfc-phones"],
    queryFn: listRfcPhones,
  });

  const usersQuery = useQuery({
    queryKey: ["admin-users"],
    queryFn: listAdminUsers,
  });

  const userRfcsQuery = useQuery({
    queryKey: ["user-rfcs", selectedUserId],
    queryFn: () => listUserRfcs(selectedUserId ?? 0),
    enabled: Boolean(selectedUserId),
  });

  const userRfcCatalogsQuery = useQuery({
    queryKey: ["user-rfcs-catalogos"],
    queryFn: listUserRfcCatalogs,
  });

  const upsertCredentialsMutation = useMutation({
    mutationFn: upsertSatCredentials,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["sat-credentials"] });
    },
  });

  const deleteCredentialsMutation = useMutation({
    mutationFn: deleteSatCredentials,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["sat-credentials"] });
    },
  });

  const upsertPhoneMutation = useMutation({
    mutationFn: upsertRfcPhone,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["rfc-phones"] });
    },
  });

  const deletePhoneMutation = useMutation({
    mutationFn: deleteRfcPhone,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["rfc-phones"] });
    },
  });

  const addUserRfcMutation = useMutation({
    mutationFn: addUserRfc,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["user-rfcs", selectedUserId],
      });
    },
  });

  const deleteUserRfcMutation = useMutation({
    mutationFn: ({ userId, rfcValue }: { userId: number; rfcValue: string }) =>
      deleteUserRfc(userId, rfcValue),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["user-rfcs", selectedUserId],
      });
    },
  });

  const credentials = useMemo(
    () => credentialsQuery.data ?? [],
    [credentialsQuery.data]
  );
  const rfcPhones = useMemo(
    () => phonesQuery.data ?? [],
    [phonesQuery.data]
  );
  const users = useMemo(() => usersQuery.data ?? [], [usersQuery.data]);
  const userRfcs = useMemo(
    () => userRfcsQuery.data ?? [],
    [userRfcsQuery.data]
  );

  const inferTipoPersonaFromRfc = (
    value: string
  ): "PM" | "PF" | "EXT" | null => {
    const rfcValue = value.trim().toUpperCase();
    if (!RFC_REGEX.test(rfcValue)) return null;
    if (rfcValue === "XEXX010101000") return "EXT";
    if (rfcValue.length === 12) return "PM";
    if (rfcValue.length === 13) return "PF";
    return null;
  };

  const regimenesForTipoPersona = useMemo(() => {
    const all = userRfcCatalogsQuery.data?.regimenes_fiscales ?? [];
    const filtered = userTipoPersonaClave
      ? all.filter(
          (row) => row.activo && row.tipo_persona_clave === userTipoPersonaClave
        )
      : all.filter((row) => row.activo);
    return filtered.sort((a, b) => a.clave.localeCompare(b.clave));
  }, [userRfcCatalogsQuery.data?.regimenes_fiscales, userTipoPersonaClave]);

  const onFileChange = (
    event: React.ChangeEvent<HTMLInputElement>,
    kind: "pfx" | "cert" | "key"
  ) => {
    const file = event.target.files?.[0] ?? null;
    if (kind === "pfx") setPfxFile(file);
    if (kind === "cert") setCertFile(file);
    if (kind === "key") setKeyFile(file);
  };

  const normalizeRfc = (value: string) => value.trim().toUpperCase();
  const normalizePhone = (value: string) => value.replace(/\D+/g, "");

  const handleSaveCredentials = () => {
    const rfcValue = normalizeRfc(rfc);
    setRfc(rfcValue);
    if (!rfcValue) {
      setCredentialsError("RFC requerido.");
      return;
    }
    if (!RFC_REGEX.test(rfcValue)) {
      setCredentialsError("RFC invalido.");
      return;
    }
    if (!keyPassword.trim()) {
      setCredentialsError("Password requerido.");
      return;
    }
    if (mode === "pfx" && !pfxFile) {
      setCredentialsError("Selecciona un archivo PFX.");
      return;
    }
    if (mode === "cerkey" && (!certFile || !keyFile)) {
      setCredentialsError("Selecciona .cer y .key.");
      return;
    }
    if (
      mode === "pfx" &&
      pfxFile &&
      !pfxFile.name.toLowerCase().endsWith(".pfx")
    ) {
      setCredentialsError("El archivo PFX debe tener extension .pfx.");
      return;
    }
    if (mode === "cerkey") {
      if (certFile && !certFile.name.toLowerCase().endsWith(".cer")) {
        setCredentialsError("El archivo .cer debe tener extension .cer.");
        return;
      }
      if (keyFile && !keyFile.name.toLowerCase().endsWith(".key")) {
        setCredentialsError("El archivo .key debe tener extension .key.");
        return;
      }
    }

    const form = new FormData();
    form.append("rfc", rfcValue);
    form.append("key_password", keyPassword.trim());
    if (mode === "pfx" && pfxFile) {
      form.append("pfx_file", pfxFile);
    }
    if (mode === "cerkey") {
      if (certFile) form.append("cert_file", certFile);
      if (keyFile) form.append("key_file", keyFile);
    }

    setCredentialsError(null);
    upsertCredentialsMutation.mutate(form, {
      onSuccess: () => {
        setRfc("");
        setKeyPassword("");
        setPfxFile(null);
        setCertFile(null);
        setKeyFile(null);
      },
      onError: (error) => {
        setCredentialsError(
          getErrorMessage(error, "No se pudo guardar las credenciales.")
        );
      },
    });
  };

  const handleDeleteCredential = (value: string) => {
    if (!confirm(`Eliminar credenciales SAT para ${value}?`)) return;
    deleteCredentialsMutation.mutate(value, {
      onError: (error) =>
        setCredentialsError(getErrorMessage(error, "No se pudo eliminar.")),
    });
  };

  const handleSavePhone = () => {
    const phoneValue = normalizePhone(phone);
    const rfcValue = normalizeRfc(phoneRfc);
    setPhone(phoneValue);
    setPhoneRfc(rfcValue);
    if (!phoneValue) {
      setPhoneError("Telefono requerido.");
      return;
    }
    if (!PHONE_REGEX.test(phoneValue)) {
      setPhoneError("Telefono invalido.");
      return;
    }
    if (!rfcValue) {
      setPhoneError("RFC requerido.");
      return;
    }
    if (!RFC_REGEX.test(rfcValue)) {
      setPhoneError("RFC invalido.");
      return;
    }

    setPhoneError(null);
    upsertPhoneMutation.mutate(
      { phone: phoneValue, rfc: rfcValue },
      {
        onSuccess: () => {
          setPhone("");
          setPhoneRfc("");
        },
        onError: (error) =>
          setPhoneError(
            getErrorMessage(error, "No se pudo guardar el telefono.")
          ),
      }
    );
  };

  const handleDeletePhone = (row: RfcPhone) => {
    if (!confirm("Eliminar telefono asociado?")) return;
    deletePhoneMutation.mutate(row.id, {
      onError: (error) =>
        setPhoneError(getErrorMessage(error, "No se pudo eliminar.")),
    });
  };

  const startEditPhone = (row: RfcPhone) => {
    setEditingPhoneId(row.id);
    setEditingPhone(row.phone);
    setEditingRfc(row.rfc);
    setPhoneError(null);
  };

  const cancelEditPhone = () => {
    setEditingPhoneId(null);
    setEditingPhone("");
    setEditingRfc("");
  };

  const saveEditPhone = () => {
    const phoneValue = normalizePhone(editingPhone);
    const rfcValue = normalizeRfc(editingRfc);
    if (!phoneValue) {
      setPhoneError("Telefono requerido.");
      return;
    }
    if (!PHONE_REGEX.test(phoneValue)) {
      setPhoneError("Telefono invalido.");
      return;
    }
    if (!rfcValue) {
      setPhoneError("RFC requerido.");
      return;
    }
    if (!RFC_REGEX.test(rfcValue)) {
      setPhoneError("RFC invalido.");
      return;
    }

    setPhoneError(null);
    upsertPhoneMutation.mutate(
      { phone: phoneValue, rfc: rfcValue },
      {
        onSuccess: () => {
          cancelEditPhone();
        },
        onError: (error) =>
          setPhoneError(
            getErrorMessage(error, "No se pudo guardar el telefono.")
          ),
      }
    );
  };

  const handleUserChange = (value: string) => {
    const userId = Number(value);
    if (!userId || Number.isNaN(userId)) {
      setSelectedUserId(null);
      return;
    }
    setSelectedUserId(userId);
  };

  const handleAddUserRfc = () => {
    if (!selectedUserId) {
      setUserRfcError("Selecciona un usuario.");
      return;
    }
    const rfcValue = normalizeRfc(userRfc);
    if (!rfcValue) {
      setUserRfcError("RFC requerido.");
      return;
    }
    if (!RFC_REGEX.test(rfcValue)) {
      setUserRfcError("RFC invalido.");
      return;
    }
    const tipoPersona = userTipoPersonaClave;
    if (!tipoPersona) {
      setUserRfcError("Tipo de persona requerido.");
      return;
    }
    const tipoInferido = inferTipoPersonaFromRfc(rfcValue);
    if (tipoInferido !== tipoPersona) {
      setUserRfcError("El RFC no corresponde al tipo de persona seleccionado.");
      return;
    }
    const regimen = userRegimenFiscalClave.trim();
    if (!regimen) {
      setUserRfcError("Regimen fiscal requerido.");
      return;
    }
    const regimenValido = regimenesForTipoPersona.some(
      (row) => row.clave === regimen
    );
    if (!regimenValido) {
      setUserRfcError("Regimen fiscal no valido para el tipo de persona.");
      return;
    }
    setUserRfcError(null);
    addUserRfcMutation.mutate(
      { user_id: selectedUserId, rfc: rfcValue, regimen_fiscal_clave: regimen },
      {
        onSuccess: () => {
          setUserRfc("");
          setUserTipoPersonaClave("");
          setUserRegimenFiscalClave("");
        },
        onError: (error) =>
          setUserRfcError(
            getErrorMessage(error, "No se pudo asociar el RFC.")
          ),
      }
    );
  };

  const handleRemoveUserRfc = (rfcValue: string) => {
    if (!selectedUserId) return;
    if (!confirm(`Eliminar RFC ${rfcValue} del usuario?`)) return;
    deleteUserRfcMutation.mutate(
      { userId: selectedUserId, rfcValue },
      {
        onError: (error) =>
          setUserRfcError(
            getErrorMessage(error, "No se pudo eliminar el RFC.")
          ),
      }
    );
  };

  return (
    <section className="space-y-6">
      <div
        id="rfc-users"
        className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm"
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400">
              Admin SAT
            </div>
            <h1 className="mt-2 text-2xl font-semibold text-white">
              Control de credenciales
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Gestiona PFX o CER/KEY, RFCs y telefonos asociados.
            </p>
          </div>
        </div>
      </div>

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
              onChange={(event) => setRfc(event.target.value.toUpperCase())}
              placeholder="RFC"
              autoComplete="off"
            />
          </label>
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Password
            <input
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              value={keyPassword}
              onChange={(event) => setKeyPassword(event.target.value)}
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
            onClick={() => setMode("pfx")}
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
            onClick={() => setMode("cerkey")}
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
            disabled={upsertCredentialsMutation.isPending}
            onClick={handleSaveCredentials}
          >
            {upsertCredentialsMutation.isPending
              ? "Guardando..."
              : "Guardar credenciales"}
          </button>
          {credentialsError ? (
            <span className="text-sm text-rose-400">{credentialsError}</span>
          ) : null}
        </div>
      </div>

      <div 
         id="rfc-users"
        className="rounded-2xl border border-white/10 bg-white/5 shadow-sm">
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
                  <td className="px-5 py-4 text-slate-400">
                    {row.created_at}
                  </td>
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
                        row.has_password
                          ? "bg-emerald-500/20"
                          : "bg-rose-500/20"
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
                      disabled={deleteCredentialsMutation.isPending}
                      onClick={() => handleDeleteCredential(row.rfc)}
                      aria-label="Eliminar credenciales"
                      title="Eliminar"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              ))}
              {!credentialsQuery.isLoading && credentials.length === 0 ? (
                <tr>
                  <td
                    className="px-5 py-6 text-center text-slate-400"
                    colSpan={6}
                  >
                    Sin credenciales registradas.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

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
              onChange={(event) => handleUserChange(event.target.value)}
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
              onChange={(event) => {
                setUserTipoPersonaClave(
                  event.target.value as "PM" | "PF" | "EXT" | ""
                );
                setUserRegimenFiscalClave("");
              }}
              value={userTipoPersonaClave}
              disabled={userRfcCatalogsQuery.isLoading}
            >
              <option value="">Selecciona tipo</option>
              {(userRfcCatalogsQuery.data?.tipos_persona ?? []).map((row) => (
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
              onChange={(event) => setUserRegimenFiscalClave(event.target.value)}
              value={userRegimenFiscalClave}
              disabled={userRfcCatalogsQuery.isLoading || !userTipoPersonaClave}
            >
              <option value="">Selecciona regimen</option>
              {regimenesForTipoPersona.map((row: RegimenFiscalCatalog) => (
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
              onChange={(event) => setUserRfc(event.target.value.toUpperCase())}
              placeholder="AAA010101AAA"
            />
          </label>
          <div className="flex items-end">
            <button
              className="w-full rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-sky-500/30 transition hover:shadow-md"
              type="button"
              onClick={handleAddUserRfc}
              disabled={addUserRfcMutation.isPending}
            >
              {addUserRfcMutation.isPending ? "Guardando..." : "Agregar RFC"}
            </button>
          </div>
        </div>
        {userRfcError ? (
          <p className="mt-3 text-sm text-rose-400">{userRfcError}</p>
        ) : null}
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 shadow-sm">
        <div className="border-b border-white/10 px-5 py-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Usuarios
          </div>
          <h3 className="mt-2 text-lg font-semibold text-white">
            RFCs asociados
          </h3>
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
                  <td className="px-5 py-4 font-medium text-white">
                    {row.rfc}
                  </td>
                  <td className="px-5 py-4 text-slate-300">
                    {row.tipo_persona_clave}
                  </td>
                  <td className="px-5 py-4 text-slate-300">
                    {row.regimen_fiscal_clave} - {row.regimen_fiscal_descripcion}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <button
                      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-rose-500/30 text-rose-300 transition hover:border-rose-500/60 hover:text-rose-200"
                      onClick={() => handleRemoveUserRfc(row.rfc)}
                      disabled={deleteUserRfcMutation.isPending}
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
                  <td
                    className="px-5 py-6 text-center text-slate-400"
                    colSpan={4}
                  >
                    Selecciona un usuario para ver sus RFCs.
                  </td>
                </tr>
              ) : null}
              {selectedUserId && userRfcs.length === 0 && !userRfcsQuery.isLoading ? (
                <tr>
                  <td
                    className="px-5 py-6 text-center text-slate-400"
                    colSpan={4}
                  >
                    Este usuario no tiene RFCs asociados.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div
        id="rfc-phones"
        className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
              Telefonos
            </div>
            <h3 className="mt-2 text-lg font-semibold text-white">
              Telefonos asociados a RFC
            </h3>
            <p className="text-sm text-slate-400">
              Se usa para resolver el RFC automaticamente en wa-bot.
            </p>
          </div>
          <button
            type="button"
            className="rounded-xl border border-white/10 bg-slate-950 px-4 py-2 text-xs uppercase tracking-[0.18em] text-white hover:bg-white/5"
            onClick={() => setShowPhoneForm((prev) => !prev)}
          >
            {showPhoneForm ? "Ocultar alta" : "Agregar telefono"}
          </button>
        </div>

        {showPhoneForm ? (
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
              Telefono
              <input
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="529999999999"
              />
            </label>
            <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
              RFC
              <input
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
                value={phoneRfc}
                onChange={(event) =>
                  setPhoneRfc(event.target.value.toUpperCase())
                }
                placeholder="AAA010101AAA"
              />
            </label>
            <div className="flex items-end">
              <button
                className="w-full rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-sky-500/30 transition hover:shadow-md"
                type="button"
                onClick={handleSavePhone}
                disabled={upsertPhoneMutation.isPending}
              >
                {upsertPhoneMutation.isPending ? "Guardando..." : "Agregar"}
              </button>
            </div>
          </div>
        ) : null}

        {phoneError ? (
          <p className="mt-3 text-sm text-rose-400">{phoneError}</p>
        ) : null}
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 shadow-sm">
        <div className="border-b border-white/10 px-5 py-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Telefonos
          </div>
          <h3 className="mt-2 text-lg font-semibold text-white">
            Telefonos registrados
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950 text-xs uppercase tracking-[0.18em] text-slate-400">
              <tr>
                <th className="px-5 py-3">Telefono</th>
                <th className="px-5 py-3">RFC</th>
                <th className="px-5 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {rfcPhones.map((row) => (
                <tr key={row.id}>
                  <td className="px-5 py-4">
                    {editingPhoneId === row.id ? (
                      <input
                        className="w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
                        value={editingPhone}
                        onChange={(event) => setEditingPhone(event.target.value)}
                        placeholder="529999999999"
                      />
                    ) : (
                      <span className="font-medium text-white">{row.phone}</span>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    {editingPhoneId === row.id ? (
                      <input
                        className="w-full rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
                        value={editingRfc}
                        onChange={(event) =>
                          setEditingRfc(event.target.value.toUpperCase())
                        }
                        placeholder="AAA010101AAA"
                      />
                    ) : (
                      <span className="text-slate-300">{row.rfc}</span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className="inline-flex items-center gap-2">
                      {editingPhoneId === row.id ? (
                        <>
                          <button
                            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-emerald-500/30 text-emerald-300 transition hover:border-emerald-500/60 hover:text-emerald-200"
                            disabled={upsertPhoneMutation.isPending}
                            onClick={saveEditPhone}
                            title="Guardar"
                            aria-label="Guardar"
                          >
                            <Save className="h-4 w-4" aria-hidden="true" />
                          </button>
                          <button
                            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-slate-300 transition hover:border-white/30 hover:text-white"
                            disabled={upsertPhoneMutation.isPending}
                            onClick={cancelEditPhone}
                            title="Cancelar"
                            aria-label="Cancelar"
                          >
                            <X className="h-4 w-4" aria-hidden="true" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-slate-300 transition hover:border-white/30 hover:text-white"
                            onClick={() => startEditPhone(row)}
                            title="Editar"
                            aria-label="Editar"
                          >
                            <Pencil className="h-4 w-4" aria-hidden="true" />
                          </button>
                          <button
                            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-rose-500/30 text-rose-300 transition hover:border-rose-500/60 hover:text-rose-200"
                            disabled={deletePhoneMutation.isPending}
                            onClick={() => handleDeletePhone(row)}
                            title="Eliminar"
                            aria-label="Eliminar"
                          >
                            <Trash2 className="h-4 w-4" aria-hidden="true" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {!phonesQuery.isLoading && rfcPhones.length === 0 ? (
                <tr>
                  <td
                    className="px-5 py-6 text-center text-slate-400"
                    colSpan={3}
                  >
                    Sin telefonos registrados.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
