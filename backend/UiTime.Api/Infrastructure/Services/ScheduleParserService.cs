using System.Text.RegularExpressions;
using Ical.Net;
using UiTime.Api.Core.DTOs;
using UiTime.Api.Core.Entities;

namespace UiTime.Api.Infrastructure.Services;

public class ScheduleParserService
{
    public IEnumerable<ParsedLessonDto> ParseSchedule(Stream icsStream)
    {
        var calendar = Calendar.Load(icsStream);
        var parsedLessons = new List<ParsedLessonDto>();

        foreach (var calEvent in calendar.Events)
        {
            var (location, onlineLink) = ExtractLocationAndLink(calEvent.Location);
            
            var startTime = new DateTimeOffset(calEvent.DtStart.AsUtc);
            var endTime = new DateTimeOffset(calEvent.DtEnd.AsUtc);
            
            var summary = calEvent.Summary ?? "Unknown subject";
            var subjectType = DetectSubjectType(summary);
            
            var cleanSubjectName = CleanSubjectName(summary);

            parsedLessons.Add(new ParsedLessonDto(
                SubjectNameRaw: cleanSubjectName,
                Type: subjectType,
                StartTime: startTime,
                EndTime: endTime,
                Location: location,
                OnlineLink: onlineLink
            ));
        }

        return parsedLessons;
    }

    private (string? Location, string? OnlineLink) ExtractLocationAndLink(string? rawLocation)
    {
        if (string.IsNullOrWhiteSpace(rawLocation)) 
            return (null, null);

        if (rawLocation.StartsWith("http", StringComparison.OrdinalIgnoreCase))
            return (null, rawLocation);

        return (rawLocation, null);
    }

    private SubjectType DetectSubjectType(string summary)
    {
        if (Regex.IsMatch(summary, @"\bW\d*\b")) return SubjectType.Lecture;
        if (Regex.IsMatch(summary, @"\bL\d*\b") || Regex.IsMatch(summary, @"\bLK\d*\b")) return SubjectType.Laboratory;
        if (Regex.IsMatch(summary, @"\bC\d*\b") || Regex.IsMatch(summary, @"\bCW\d*\b")) return SubjectType.Tutorial;
        if (Regex.IsMatch(summary, @"\bKW\d*\b")) return SubjectType.Seminar;
        if (Regex.IsMatch(summary, @"\bP\d*\b")) return SubjectType.Project;
        
        return SubjectType.Other; 
    }

    private string CleanSubjectName(string rawSummary)
    {
        var match = Regex.Match(rawSummary, @" \d{4} [ZL] ");
    
        if (match.Success)
        {
            return rawSummary.Substring(match.Index + match.Length).Trim();
        }
        
        return rawSummary.Trim();
    }
}