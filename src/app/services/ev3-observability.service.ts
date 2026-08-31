// src/app/services/ev3-observability.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Ev3Health,
  Ev3Metrics,
  Ev3TracesResponse,
  Ev3RecommendationsResponse,
  Ev3SecurityResult,
} from '../models/ev3-observability.models';

@Injectable({ providedIn: 'root' })
export class Ev3ObservabilityService {
  private readonly base = `${environment.aiProxyUrl}/api/ev3`;

  constructor(private http: HttpClient) {}

  getHealth(): Observable<Ev3Health> {
    return this.http.get<Ev3Health>(`${this.base}/health`);
  }

  getMetrics(): Observable<Ev3Metrics> {
    return this.http.get<Ev3Metrics>(`${this.base}/metrics`);
  }

  getTraces(): Observable<Ev3TracesResponse> {
    return this.http.get<Ev3TracesResponse>(`${this.base}/traces`);
  }

  getRecommendations(): Observable<Ev3RecommendationsResponse> {
    return this.http.get<Ev3RecommendationsResponse>(
      `${this.base}/recommendations`,
    );
  }

  securityCheck(message: string): Observable<Ev3SecurityResult> {
    const params = new HttpParams().set('message', message);
    return this.http.get<Ev3SecurityResult>(`${this.base}/security-check`, {
      params,
    });
  }
}
