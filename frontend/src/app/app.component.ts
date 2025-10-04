import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

interface Message {
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  data?: any;
}

interface Alert {
  equipment_name: string;
  message: string;
  severity: string;
  days_until?: number;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'AI Mining Operations Co-Pilot';
  
  messages: Message[] = [];
  userInput = '';
  isLoading = false;
  
  alerts: Alert[] = [];
  equipmentData: any[] = [];
  productionData: any[] = [];
  carbonFootprint: any = {};
  
  fuelChart: any;
  productionChart: any;

  private backendUrl = 'http://localhost:5000';
  private groqApiKey = '';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    // AUTH CHECK - Redirect to login if no token
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login.html';
      return;
    }

    // Load dashboard data
    this.loadDashboardData();
    this.loadAlerts();
    
    this.messages.push({
      text: 'Hello! I\'m your AI Mining Operations Co-Pilot. Ask me about fuel consumption, maintenance schedules, production efficiency, or carbon emissions.',
      sender: 'ai',
      timestamp: new Date()
    });
  }

  loadDashboardData() {
    this.http.get(`${this.backendUrl}/api/data`).subscribe({
      next: (response: any) => {
        this.equipmentData = response.equipment || [];
        this.productionData = response.production || [];
        this.carbonFootprint = response.carbon_footprint || {};
        
        setTimeout(() => {
          this.initializeCharts();
        }, 100);
      },
      error: (error) => {
        console.error('Error loading dashboard data:', error);
      }
    });
  }

  loadAlerts() {
    this.http.get(`${this.backendUrl}/api/alerts`).subscribe({
      next: (response: any) => {
        this.alerts = response.alerts || [];
      },
      error: (error) => {
        console.error('Error loading alerts:', error);
      }
    });
  }

  async sendMessage() {
    if (!this.userInput.trim() || this.isLoading) return;

    const userMessage: Message = {
      text: this.userInput,
      sender: 'user',
      timestamp: new Date()
    };

    this.messages.push(userMessage);
    const query = this.userInput;
    this.userInput = '';
    this.isLoading = true;

    try {
      const response = await this.processQueryWithLangChain(query);
      
      const aiMessage: Message = {
        text: response.answer,
        sender: 'ai',
        timestamp: new Date(),
        data: response.data
      };

      this.messages.push(aiMessage);
    } catch (error) {
      console.error('Error processing query:', error);
      
      this.messages.push({
        text: 'I encountered an error processing your request. Please try again.',
        sender: 'ai',
        timestamp: new Date()
      });
    } finally {
      this.isLoading = false;
    }
  }

  async processQueryWithLangChain(query: string): Promise<any> {
    try {
      const response = await this.http.post(`${this.backendUrl}/api/query`, { query }).toPromise();
      return {
        answer: (response as any).response,
        data: (response as any).data
      };
    } catch (error) {
      console.error('Backend query error:', error);
      throw error;
    }
  }

  initializeCharts() {
    this.createFuelChart();
    this.createProductionChart();
  }

  createFuelChart() {
    const canvas = document.getElementById('fuelChart') as HTMLCanvasElement;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (this.fuelChart) {
      this.fuelChart.destroy();
    }

    const fuelData = this.equipmentData.map(eq => ({
      name: eq.name,
      efficiency: eq.fuel_efficiency
    }));

    this.fuelChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: fuelData.map(d => d.name),
        datasets: [{
          label: 'Fuel Efficiency (L/hr)',
          data: fuelData.map(d => d.efficiency),
          backgroundColor: 'rgba(50, 130, 184, 0.6)',
          borderColor: 'rgba(50, 130, 184, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#e0e0e0' }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { color: '#e0e0e0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
          },
          x: {
            ticks: { color: '#e0e0e0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
          }
        }
      }
    });
  }

  createProductionChart() {
    const canvas = document.getElementById('productionChart') as HTMLCanvasElement;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (this.productionChart) {
      this.productionChart.destroy();
    }

    this.productionChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: this.productionData.map(d => d.date),
        datasets: [
          {
            label: 'Ore Extracted (tons)',
            data: this.productionData.map(d => d.ore_extracted_tons),
            borderColor: 'rgba(39, 174, 96, 1)',
            backgroundColor: 'rgba(39, 174, 96, 0.2)',
            tension: 0.4,
            fill: true
          },
          {
            label: 'Target (tons)',
            data: this.productionData.map(d => d.target_tons),
            borderColor: 'rgba(243, 156, 18, 1)',
            backgroundColor: 'rgba(243, 156, 18, 0.2)',
            tension: 0.4,
            fill: false,
            borderDash: [5, 5]
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#e0e0e0' }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { color: '#e0e0e0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
          },
          x: {
            ticks: { color: '#e0e0e0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
          }
        }
      }
    });
  }

  getAlertClass(severity: string): string {
    switch (severity) {
      case 'high': return 'alert-high';
      case 'medium': return 'alert-medium';
      default: return 'alert-low';
    }
  }
}