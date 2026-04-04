using UiTime.Api.Core.DTOs;

namespace UiTime.Api.Infrastructure.Services;

public interface IScheduleParserService
{
    public IEnumerable<ParsedLessonDto> ParseSchedule(Stream icsStream);
}