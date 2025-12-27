{{/*
Expand the name of the chart.
*/}}
{{- define "coins-for-change.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "coins-for-change.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "coins-for-change.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "coins-for-change.labels" -}}
helm.sh/chart: {{ include "coins-for-change.chart" . }}
{{ include "coins-for-change.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "coins-for-change.selectorLabels" -}}
app.kubernetes.io/name: {{ include "coins-for-change.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "coins-for-change.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "coins-for-change.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "coins-for-change.postgresql.host" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgresql" (include "coins-for-change.fullname" .) }}
{{- else }}
{{- .Values.database.external.host }}
{{- end }}
{{- end }}

{{/*
PostgreSQL port
*/}}
{{- define "coins-for-change.postgresql.port" -}}
{{- if .Values.postgresql.enabled }}
{{- 5432 }}
{{- else }}
{{- .Values.database.external.port }}
{{- end }}
{{- end }}

{{/*
PostgreSQL database name
*/}}
{{- define "coins-for-change.postgresql.database" -}}
{{- if .Values.postgresql.enabled }}
{{- .Values.postgresql.auth.database }}
{{- else }}
{{- .Values.database.external.database }}
{{- end }}
{{- end }}

{{/*
PostgreSQL username
*/}}
{{- define "coins-for-change.postgresql.username" -}}
{{- if .Values.postgresql.enabled }}
{{- .Values.postgresql.auth.username }}
{{- else }}
{{- .Values.database.external.username }}
{{- end }}
{{- end }}