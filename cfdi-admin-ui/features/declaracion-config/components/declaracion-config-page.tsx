"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";

import {
  getDeclaracionConfig,
  listDeclaracionConfigCatalogs,
  upsertDeclaracionConfig,
} from "../api";
import type { DeclaracionUsoCatalog, TipoDeclaracionClave } from "../types";
import { getErrorMessage } from "@/lib/errors";

type ApiLikeError = {
  status?: number;
};

function hasHttpStatus(error: unknown): error is ApiLikeError {
  return Boolean(error && typeof error === "object" && "status" in error);
}

export default function DeclaracionConfigPage() {
  const queryClient = useQueryClient();

  const [regimenFiscalClave, setRegimenFiscalClave] = useState("");
  const [tipoDeclaracion, setTipoDeclaracion] = useState<TipoDeclaracionClave>("MENSUAL");
  const [usoToAdd, setUsoToAdd] = useState("");
  const [usosSeleccionadosLocal, setUsosSeleccionadosLocal] = useState<DeclaracionUsoCatalog[] | null>(null);
  const [activoLocal, setActivoLocal] = useState<boolean | null>(null);
  const [incluirAcumuladoLocal, setIncluirAcumuladoLocal] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const catalogsQuery = useQuery({
    queryKey: ["declaracion-config-catalogos"],
    queryFn: listDeclaracionConfigCatalogs,
  });

  const configQuery = useQuery({
    queryKey: ["declaracion-config", regimenFiscalClave, tipoDeclaracion],
    queryFn: () => getDeclaracionConfig(regimenFiscalClave, tipoDeclaracion),
    enabled: Boolean(regimenFiscalClave && tipoDeclaracion),
    retry: false,
  });

  const saveMutation = useMutation({
    mutationFn: upsertDeclaracionConfig,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["declaracion-config", regimenFiscalClave, tipoDeclaracion],
      });
    },
  });

  const regimenesActivos = useMemo(() => {
    const all = catalogsQuery.data?.regimenes_fiscales ?? [];
    return all.filter((row) => row.activo).sort((a, b) => a.clave.localeCompare(b.clave));
  }, [catalogsQuery.data?.regimenes_fiscales]);

  const tiposActivos = useMemo(() => {
    const all = catalogsQuery.data?.tipos_declaracion ?? [];
    return all.filter((row) => row.activo);
  }, [catalogsQuery.data?.tipos_declaracion]);

  const usosDelTipo = useMemo(() => {
    const all = catalogsQuery.data?.usos_cfdi_deduccion ?? [];
    return all
      .filter((row) => row.activo && row.tipo_declaracion_clave === tipoDeclaracion)
      .sort((a, b) => a.clave.localeCompare(b.clave));
  }, [catalogsQuery.data?.usos_cfdi_deduccion, tipoDeclaracion]);

  const usosSeleccionadosBase = useMemo(() => {
    if (configQuery.data) {
      return configQuery.data.usos_cfdi
        .map((row) => usosDelTipo.find((catalog) => catalog.clave === row.clave))
        .filter((row): row is DeclaracionUsoCatalog => Boolean(row));
    }
    if (configQuery.error && hasHttpStatus(configQuery.error) && configQuery.error.status === 404) {
      return [];
    }
    return [];
  }, [configQuery.data, configQuery.error, usosDelTipo]);

  const usosSeleccionados = usosSeleccionadosLocal ?? usosSeleccionadosBase;
  const activo = activoLocal ?? configQuery.data?.activo ?? true;
  const incluirAcumuladoMensualEnAnual =
    incluirAcumuladoLocal ?? configQuery.data?.incluir_acumulado_mensual_en_anual ?? true;

  const usosDisponibles = useMemo(() => {
    const selected = new Set(usosSeleccionados.map((row) => row.clave));
    return usosDelTipo.filter((row) => !selected.has(row.clave));
  }, [usosDelTipo, usosSeleccionados]);

  const resetEditorState = () => {
    setUsoToAdd("");
    setUsosSeleccionadosLocal(null);
    setActivoLocal(null);
    setIncluirAcumuladoLocal(null);
    setSuccess(null);
    setError(null);
  };

  const handleAddUso = () => {
    if (!usoToAdd) return;
    const item = usosDelTipo.find((row) => row.clave === usoToAdd);
    if (!item) {
      setError("Uso CFDI invalido para el tipo seleccionado.");
      return;
    }
    setUsosSeleccionadosLocal([...(usosSeleccionadosLocal ?? usosSeleccionadosBase), item]);
    setUsoToAdd("");
    setError(null);
    setSuccess(null);
  };

  const handleRemoveUso = (clave: string) => {
    setUsosSeleccionadosLocal((usosSeleccionadosLocal ?? usosSeleccionadosBase).filter((row) => row.clave !== clave));
    setError(null);
    setSuccess(null);
  };

  const handleSave = () => {
    if (!regimenFiscalClave) {
      setError("Selecciona un regimen fiscal.");
      return;
    }
    if (usosSeleccionados.length === 0) {
      setError("Agrega al menos un uso CFDI para el tipo seleccionado.");
      return;
    }

    setError(null);
    setSuccess(null);
    saveMutation.mutate(
      {
        regimen_fiscal_clave: regimenFiscalClave,
        tipo_declaracion_clave: tipoDeclaracion,
        activo,
        incluir_acumulado_mensual_en_anual: incluirAcumuladoMensualEnAnual,
        usos_cfdi: usosSeleccionados.map((row, idx) => ({ clave: row.clave, orden: idx + 1 })),
      },
      {
        onSuccess: () => {
          setUsosSeleccionadosLocal(null);
          setActivoLocal(null);
          setIncluirAcumuladoLocal(null);
          setSuccess("Configuracion guardada.");
        },
        onError: (err) => {
          setError(getErrorMessage(err, "No se pudo guardar la configuracion."));
        },
      }
    );
  };

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Declaracion</div>
        <h1 className="mt-2 text-2xl font-semibold text-white">Configuracion por regimen</h1>
        <p className="mt-1 text-sm text-slate-400">
          Administra unicamente los usos CFDI permitidos por tipo de declaracion.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">        
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">

          <div className="grid gap-4 pb-5">
            <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
              Regimen fiscal
              <select
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
                value={regimenFiscalClave}
                onChange={(event) => {
                  setRegimenFiscalClave(event.target.value);
                  resetEditorState();
                }}
              >
                <option value="">Selecciona regimen</option>
                {regimenesActivos.map((row) => (
                  <option key={`${row.clave}-${row.tipo_persona_clave}`} value={row.clave}>
                    {row.clave} - {row.descripcion}
                  </option>
                ))}
              </select>
            </label>       
          </div>

          <div className="text-xs uppercase tracking-[0.18em] text-slate-400 pb-5">
            Tipo declaracion
            <select
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              value={tipoDeclaracion}
              onChange={(event) => {
                setTipoDeclaracion(event.target.value as TipoDeclaracionClave);
                resetEditorState();
              }}
            >
              {tiposActivos.map((row) => (
                <option key={row.clave} value={row.clave}>
                  {row.clave}
                </option>
              ))}
            </select>
          </div>

          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Agregar Usos CFDI</div>  
          
          <div className="mt-3 flex gap-2">
            <select
              className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
              value={usoToAdd}
              onChange={(event) => setUsoToAdd(event.target.value)}
              disabled={!regimenFiscalClave}
            >
              <option value="">Selecciona uso CFDI</option>
              {usosDisponibles.map((row) => (
                <option key={row.clave} value={row.clave}>
                  {row.clave} - {row.descripcion}
                </option>
              ))}
            </select>
            <button
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-500/40 text-emerald-300 transition hover:border-emerald-500/70 hover:text-emerald-200"
              type="button"
              onClick={handleAddUso}
              disabled={!usoToAdd || !regimenFiscalClave}
              aria-label="Agregar uso CFDI"
              title="Agregar"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>

          <div className="flex items-end gap-2 pt-5">
            <button
              className="w-full rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-sky-500/30 transition hover:shadow-md"
              type="button"
              onClick={handleSave}
              disabled={saveMutation.isPending || !regimenFiscalClave}
            >
              {saveMutation.isPending ? "Guardando..." : "Guardar"}
            </button>
          </div>

          {error ? <p className="mt-3 text-sm text-rose-400">{error}</p> : null}
          {success ? <p className="mt-3 text-sm text-emerald-300">{success}</p> : null}
          {catalogsQuery.isLoading ? (
            <p className="mt-3 text-sm text-slate-400">Cargando catalogos...</p>
          ) : null}
          {catalogsQuery.error ? (
            <p className="mt-3 text-sm text-rose-400">
              {getErrorMessage(catalogsQuery.error, "No se pudieron cargar catalogos.")}
            </p>
          ) : null}
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Usos configurados</div>
          <h2 className="mt-2 text-lg font-semibold text-white">Lista actual</h2>
          {configQuery.isLoading ? <p className="mt-3 text-sm text-slate-400">Cargando configuracion...</p> : null}
          {usosSeleccionados.length === 0 ? (
            <p className="mt-3 text-sm text-slate-400">Sin usos seleccionados.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {usosSeleccionados.map((row) => (
                <li
                  key={row.clave}
                  className="flex items-center justify-between rounded-xl border border-white/10 bg-slate-950 px-3 py-2"
                >
                  <span className="text-sm text-white">
                    {row.clave} - {row.descripcion}
                  </span>
                  <button
                    className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-rose-500/30 text-rose-300 transition hover:border-rose-500/60 hover:text-rose-200"
                    type="button"
                    onClick={() => handleRemoveUso(row.clave)}
                    aria-label={`Eliminar ${row.clave}`}
                    title="Eliminar"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
