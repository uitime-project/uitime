using UiTime.Api.Core.Entities;

namespace UiTime.Api.Core.DTOs;

public record ParsedLessonDto(
    string SubjectNameRaw,
    SubjectType Type,
    DateTimeOffset StartTime,
    DateTimeOffset EndTime,
    string? Location,
    string? OnlineLink);