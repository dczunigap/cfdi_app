import { Component, OnInit } from '@angular/core';
import { AsyncPipe, DatePipe, DecimalPipe, NgFor, NgIf } from '@angular/common';

import { facturas$ } from '../data/facturas.queries';
import { FacturasRepository } from '../data/facturas.repository';

@Component({
  selector: 'app-facturas-page',
  standalone: true,
  imports: [AsyncPipe, DatePipe, DecimalPipe, NgFor, NgIf],
  templateUrl: './facturas-page.component.html',
  styleUrl: './facturas-page.component.css',
})
export class FacturasPageComponent implements OnInit {
  readonly facturas$ = facturas$;

  constructor(private readonly repo: FacturasRepository) {}

  ngOnInit(): void {
    this.repo.fetch();
  }
}
