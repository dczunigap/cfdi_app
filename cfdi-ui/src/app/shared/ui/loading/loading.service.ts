import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class LoadingService {
  private readonly counter = new BehaviorSubject(0);
  readonly isLoading$ = this.counter.asObservable();

  show(): void {
    this.counter.next(this.counter.value + 1);
  }

  hide(): void {
    this.counter.next(Math.max(0, this.counter.value - 1));
  }
}
