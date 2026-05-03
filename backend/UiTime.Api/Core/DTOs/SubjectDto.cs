using UiTime.Api.Core.Entities;

namespace UiTime.Api.Core.DTOs;

public record SubjectDto
(
    Guid Id,
    string Name,
    SubjectType Type,
    bool? HasExam,
    DateTimeOffset? ExamDate
);