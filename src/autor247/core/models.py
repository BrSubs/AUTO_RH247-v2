"""Enums e modelos de status da aplicação."""

from enum import Enum


class StatusAbono(str, Enum):
    OK = "OK"
    ERRO = "ERRO"
    NOT_FOUND = "NOT FOUND"
    MULTIPLE_CHOICES = "MULTIPLE CHOICES"
    CONFLITO = "CONFLITO"
    TIMEOUT = "TIMEOUT"
    DELETE = "DELETE"
    DELETED = "DELETED"
    PENDENTE = ""
