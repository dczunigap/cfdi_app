import { Injectable, Injector, inject } from '@angular/core';
import { Overlay, OverlayRef } from '@angular/cdk/overlay';
import { ComponentPortal } from '@angular/cdk/portal';
import { BehaviorSubject } from 'rxjs';

import { ToastContainerComponent } from './toast-container.component';
import { AlertAppearance } from './alert.service';

export interface ToastItem {
  id: number;
  appearance: AlertAppearance;
  title: string;
  message: string;
  dismissible: boolean;
  durationMs: number;
}

@Injectable({ providedIn: 'root' })
export class ToastService {
  private readonly overlay = inject(Overlay);
  private readonly injector = inject(Injector);

  private readonly items$ = new BehaviorSubject<ToastItem[]>([]);
  private overlayRef: OverlayRef | null = null;
  private nextId = 1;

  get stream() {
    return this.items$.asObservable();
  }

  show(item: Omit<ToastItem, 'id'>): void {
    this.ensureOverlay();
    const id = this.nextId++;
    const entry: ToastItem = { ...item, id };
    this.items$.next([...this.items$.getValue(), entry]);

    if (item.durationMs > 0) {
      setTimeout(() => this.dismiss(id), item.durationMs);
    }
  }

  dismiss(id: number): void {
    const items = this.items$.getValue().filter((item) => item.id !== id);
    this.items$.next(items);
  }

  private ensureOverlay(): void {
    if (this.overlayRef) return;
    const positionStrategy = this.overlay
      .position()
      .global()
      .top('1rem')
      .right('1rem');
    this.overlayRef = this.overlay.create({
      positionStrategy,
      scrollStrategy: this.overlay.scrollStrategies.noop(),
      hasBackdrop: false,
      panelClass: 'app-toast-overlay',
    });
    this.overlayRef.attach(new ComponentPortal(ToastContainerComponent, null, this.injector));
  }
}
