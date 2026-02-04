"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";

import { addPlatformRfc, deletePlatformRfc, listPlatformRfcs } from "../api";
import { getErrorMessage } from "@/lib/errors";

const RFC_REGEX = /^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$/;

export default function PlatformRfcsPage() {
  const queryClient = useQueryClient();

  const [newRfc, setNewRfc] = useState("");
  const [newNombre, setNewNombre] = useState("");
  const [error, setError] = useState<string | null>(null);

  const rfcsQuery = useQuery({
    queryKey: ["platform-rfcs"],
    queryFn: listPlatformRfcs,
  });

  const addMutation = useMutation({
    mutationFn: addPlatformRfc,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["platform-rfcs"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deletePlatformRfc,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["platform-rfcs"] });
    },
  });

  const platformRfcs = useMemo(() => rfcsQuery.data ?? [], [rfcsQuery.data]);

  const handleAdd = () => {
    const rfc = newRfc.trim().toUpperCase();
    const nombre = newNombre.trim();
    if (!rfc) {
      setError("RFC requerido.");
      return;
    }
    if (!RFC_REGEX.test(rfc)) {
      setError("RFC invalido.");
      return;
    }

    setError(null);
    addMutation.mutate(
      { rfc, nombre: nombre || null },
      {
        onSuccess: () => {
          setNewRfc("");
          setNewNombre("");
        },
        onError: (err) =>
          setError(getErrorMessage(err, "No se pudo guardar el RFC.")),
      }
    );
  };

  const handleDelete = (id: number) => {
    if (!confirm("Eliminar RFC de plataforma?")) return;
    deleteMutation.mutate(id, {
      onError: (err) =>
        setError(getErrorMessage(err, "No se pudo eliminar el RFC.")),
    });
  };

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400">
              Plataformas
            </div>
            <h1 className="mt-2 text-2xl font-semibold text-white">
              RFCs de plataforma
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Lista usada para evitar doble conteo de CFDI emitidos a plataformas.
            </p>
          </div>
          <span className="rounded-full border border-white/10 bg-slate-950 px-3 py-1 text-xs text-slate-400">
            Control SAT
          </span>
        </div>
      </div>

      <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 px-5 py-4 text-sm text-emerald-200 shadow-sm">
        Se cargan automaticamente al importar XML de retenciones. Puedes agregar o eliminar manualmente.
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
        <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
          Plataformas
        </div>
        <h2 className="text-lg font-semibold text-white">Agregar RFC</h2>
        <div className="mt-3 grid gap-4 md:grid-cols-3">
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            RFC
            <input
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              value={newRfc}
              onChange={(event) => setNewRfc(event.target.value.toUpperCase())}
              placeholder="AAA010101AAA"
            />
          </label>
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Nombre
            <input
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              value={newNombre}
              onChange={(event) => setNewNombre(event.target.value)}
              placeholder="Nombre de plataforma"
            />
          </label>
          <div className="flex items-end">
            <button
              className="w-full rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-sky-500/30 transition hover:shadow-md"
              type="button"
              onClick={handleAdd}
              disabled={addMutation.isPending}
            >
              {addMutation.isPending ? "Guardando..." : "Agregar"}
            </button>
          </div>
        </div>
        {error ? <p className="mt-3 text-sm text-rose-400">{error}</p> : null}
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 shadow-sm">
        <div className="border-b border-white/10 px-5 py-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Plataformas
          </div>
          <h3 className="mt-2 text-lg font-semibold text-white">
            RFCs registrados
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950 text-xs uppercase tracking-[0.18em] text-slate-400">
              <tr>
                <th className="px-5 py-3">RFC</th>
                <th className="px-5 py-3">Nombre</th>
                <th className="px-5 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {platformRfcs.map((item) => (
                <tr key={item.id}>
                  <td className="px-5 py-4 font-medium text-white">
                    {item.rfc}
                  </td>
                  <td className="px-5 py-4 text-slate-300">
                    {item.nombre || "-"}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <button
                      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-rose-500/30 text-rose-300 transition hover:border-rose-500/60 hover:text-rose-200"
                      type="button"
                      onClick={() => handleDelete(item.id)}
                      disabled={deleteMutation.isPending}
                      aria-label="Eliminar"
                      title="Eliminar"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              ))}
              {!rfcsQuery.isLoading && platformRfcs.length === 0 ? (
                <tr>
                  <td
                    className="px-5 py-6 text-center text-slate-400"
                    colSpan={3}
                  >
                    Sin RFCs registrados.
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
