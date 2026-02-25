import { Component, Input, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { RfcService } from '../../../core/rfc/rfc.service';

@Component({
  selector: 'app-rfc-selector',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './rfc-selector.component.html',
})
export class RfcSelectorComponent {
  readonly rfcService = inject(RfcService);

  @Input() collapsed = false;
  @Input() label = 'RFC activo';
  @Input() showBadge = true;
}
