import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';

import { API_BASE_URL } from '../api/api-client';

const STORAGE_KEY = 'cfdi.rfc.selected';

type SatCredentialResponse = {
  rfc: string;
  created_at: string;
  updated_at?: string | null;
  has_password: boolean;
  has_pfx: boolean;
};

@Injectable({ providedIn: 'root' })
export class RfcService {
  private readonly selected = signal<string | null>(this.readStored());
  private readonly options = signal<string[]>([]);

  constructor(private readonly http: HttpClient) {}

  selectedRfc() {
    return this.selected();
  }

  optionsList() {
    return this.options();
  }

  setSelected(rfc: string | null) {
    const value = rfc?.trim().toUpperCase() || null;
    this.selected.set(value);
    if (value) {
      localStorage.setItem(STORAGE_KEY, value);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  refreshOptions() {
    this.http.get<SatCredentialResponse[]>(`${API_BASE_URL}/sat/credentials`).subscribe({
      next: (rows) => {
        const rfcs = rows.map((row) => row.rfc).filter(Boolean);
        const stored = this.readStored();
        let selected = this.selected() || stored;
        const merged = selected && !rfcs.includes(selected) ? [selected, ...rfcs] : rfcs;
        this.options.set(merged);
        if (selected) {
          this.selected.set(selected);
        }
      },
      error: () => {
        this.options.set([]);
      }
    });
  }

  private readStored() {
    const value = localStorage.getItem(STORAGE_KEY);
    return value ? value.trim().toUpperCase() : null;
  }
}
