import { Routes } from '@angular/router';
import { AuthGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    canActivate: [AuthGuard],
    children: [
      // Add your actual components here
      // Example:
      // { path: 'dashboard', component: DashboardComponent },
      // { path: 'operations', component: OperationsComponent },
    ]
  }
];