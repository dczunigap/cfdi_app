import { Pencil, Save, Trash2, X } from "lucide-react";

import type { RfcPhone } from "../types";

type PhonesSectionProps = {
  phone: string;
  phoneRfc: string;
  phoneError: string | null;
  showPhoneForm: boolean;
  editingPhoneId: number | null;
  editingPhone: string;
  editingRfc: string;
  rfcPhones: RfcPhone[];
  isPhonesLoading: boolean;
  isSavingPhone: boolean;
  isDeletingPhone: boolean;
  onTogglePhoneForm: () => void;
  onSetPhone: (value: string) => void;
  onSetPhoneRfc: (value: string) => void;
  onSavePhone: () => void;
  onSetEditingPhone: (value: string) => void;
  onSetEditingRfc: (value: string) => void;
  onStartEditPhone: (row: RfcPhone) => void;
  onCancelEditPhone: () => void;
  onSaveEditPhone: () => void;
  onDeletePhone: (row: RfcPhone) => void;
};

export default function PhonesSection(props: PhonesSectionProps) {
  const {
    phone,
    phoneRfc,
    phoneError,
    showPhoneForm,
    editingPhoneId,
    editingPhone,
    editingRfc,
    rfcPhones,
    isPhonesLoading,
    isSavingPhone,
    isDeletingPhone,
    onTogglePhoneForm,
    onSetPhone,
    onSetPhoneRfc,
    onSavePhone,
    onSetEditingPhone,
    onSetEditingRfc,
    onStartEditPhone,
    onCancelEditPhone,
    onSaveEditPhone,
    onDeletePhone,
  } = props;

  return (
    <>
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
              Se usa para resolver el RFC automaticamente en cfdi-wa-bot.
            </p>
          </div>
          <button
            type="button"
            className="rounded-xl border border-white/10 bg-slate-950 px-4 py-2 text-xs uppercase tracking-[0.18em] text-white hover:bg-white/5"
            onClick={onTogglePhoneForm}
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
                onChange={(event) => onSetPhone(event.target.value)}
                placeholder="529999999999"
              />
            </label>
            <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
              RFC
              <input
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
                value={phoneRfc}
                onChange={(event) => onSetPhoneRfc(event.target.value.toUpperCase())}
                placeholder="AAA010101AAA"
              />
            </label>
            <div className="flex items-end">
              <button
                className="w-full rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-sky-500/30 transition hover:shadow-md"
                type="button"
                onClick={onSavePhone}
                disabled={isSavingPhone}
              >
                {isSavingPhone ? "Guardando..." : "Agregar"}
              </button>
            </div>
          </div>
        ) : null}

        {phoneError ? <p className="mt-3 text-sm text-rose-400">{phoneError}</p> : null}
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
                        onChange={(event) => onSetEditingPhone(event.target.value)}
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
                        onChange={(event) => onSetEditingRfc(event.target.value.toUpperCase())}
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
                            disabled={isSavingPhone}
                            onClick={onSaveEditPhone}
                            title="Guardar"
                            aria-label="Guardar"
                          >
                            <Save className="h-4 w-4" aria-hidden="true" />
                          </button>
                          <button
                            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-slate-300 transition hover:border-white/30 hover:text-white"
                            disabled={isSavingPhone}
                            onClick={onCancelEditPhone}
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
                            onClick={() => onStartEditPhone(row)}
                            title="Editar"
                            aria-label="Editar"
                          >
                            <Pencil className="h-4 w-4" aria-hidden="true" />
                          </button>
                          <button
                            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-rose-500/30 text-rose-300 transition hover:border-rose-500/60 hover:text-rose-200"
                            disabled={isDeletingPhone}
                            onClick={() => onDeletePhone(row)}
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
              {!isPhonesLoading && rfcPhones.length === 0 ? (
                <tr>
                  <td className="px-5 py-6 text-center text-slate-400" colSpan={3}>
                    Sin telefonos registrados.
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
