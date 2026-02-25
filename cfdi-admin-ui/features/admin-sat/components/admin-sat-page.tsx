"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

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
import type { RfcPhone } from "../types";
import { getErrorMessage } from "@/lib/errors";
import {
  isValidPhone,
  isValidRfc,
  normalizePhone,
  normalizeRfc,
} from "../utils/validators";
import CredentialsSection from "./credentials-section";
import UserRfcsSection from "./user-rfcs-section";
import PhonesSection from "./phones-section";

type UploadMode = "pfx" | "cerkey";

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
    const rfcValue = normalizeRfc(value);
    if (!isValidRfc(rfcValue)) return null;
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

  const handleSaveCredentials = () => {
    const rfcValue = normalizeRfc(rfc);
    setRfc(rfcValue);
    if (!rfcValue) {
      setCredentialsError("RFC requerido.");
      return;
    }
    if (!isValidRfc(rfcValue)) {
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
    if (!isValidPhone(phoneValue)) {
      setPhoneError("Telefono invalido.");
      return;
    }
    if (!rfcValue) {
      setPhoneError("RFC requerido.");
      return;
    }
    if (!isValidRfc(rfcValue)) {
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
    if (!isValidPhone(phoneValue)) {
      setPhoneError("Telefono invalido.");
      return;
    }
    if (!rfcValue) {
      setPhoneError("RFC requerido.");
      return;
    }
    if (!isValidRfc(rfcValue)) {
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
    if (!isValidRfc(rfcValue)) {
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

      <CredentialsSection
        mode={mode}
        rfc={rfc}
        keyPassword={keyPassword}
        credentialsError={credentialsError}
        credentials={credentials}
        isLoadingCredentials={credentialsQuery.isLoading}
        isSavingCredentials={upsertCredentialsMutation.isPending}
        isDeletingCredentials={deleteCredentialsMutation.isPending}
        onSetMode={setMode}
        onSetRfc={setRfc}
        onSetKeyPassword={setKeyPassword}
        onFileChange={onFileChange}
        onSaveCredentials={handleSaveCredentials}
        onDeleteCredential={handleDeleteCredential}
      />

      <UserRfcsSection
        users={users}
        tiposPersona={userRfcCatalogsQuery.data?.tipos_persona ?? []}
        regimenesForTipoPersona={regimenesForTipoPersona}
        userRfcs={userRfcs}
        selectedUserId={selectedUserId}
        userTipoPersonaClave={userTipoPersonaClave}
        userRegimenFiscalClave={userRegimenFiscalClave}
        userRfc={userRfc}
        userRfcError={userRfcError}
        isCatalogsLoading={userRfcCatalogsQuery.isLoading}
        isAddPending={addUserRfcMutation.isPending}
        isDeletePending={deleteUserRfcMutation.isPending}
        isUserRfcsLoading={userRfcsQuery.isLoading}
        onUserChange={handleUserChange}
        onUserTipoPersonaChange={(value) => {
          setUserTipoPersonaClave(value);
          setUserRegimenFiscalClave("");
        }}
        onUserRegimenFiscalChange={setUserRegimenFiscalClave}
        onUserRfcChange={setUserRfc}
        onAddUserRfc={handleAddUserRfc}
        onRemoveUserRfc={handleRemoveUserRfc}
      />

      <PhonesSection
        phone={phone}
        phoneRfc={phoneRfc}
        phoneError={phoneError}
        showPhoneForm={showPhoneForm}
        editingPhoneId={editingPhoneId}
        editingPhone={editingPhone}
        editingRfc={editingRfc}
        rfcPhones={rfcPhones}
        isPhonesLoading={phonesQuery.isLoading}
        isSavingPhone={upsertPhoneMutation.isPending}
        isDeletingPhone={deletePhoneMutation.isPending}
        onTogglePhoneForm={() => setShowPhoneForm((prev) => !prev)}
        onSetPhone={setPhone}
        onSetPhoneRfc={setPhoneRfc}
        onSavePhone={handleSavePhone}
        onSetEditingPhone={setEditingPhone}
        onSetEditingRfc={setEditingRfc}
        onStartEditPhone={startEditPhone}
        onCancelEditPhone={cancelEditPhone}
        onSaveEditPhone={saveEditPhone}
        onDeletePhone={handleDeletePhone}
      />
    </section>
  );
}
