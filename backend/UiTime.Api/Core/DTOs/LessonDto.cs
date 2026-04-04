using UiTime.Api.Core.Entities;

namespace UiTime.Api.Core.DTOs;

public record LessonDto(
    Guid Id,
    string SubjectName,
    SubjectType SubjectType,
    DateTimeOffset StartTime,
    DateTimeOffset EndTime,
    string? Location,
    string? OnlineLink
);