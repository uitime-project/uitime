using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using UiTime.Api.Core.DTOs;
using UiTime.Api.Core.Entities;
using UiTime.Api.Infrastructure.Data;
using UiTime.Api.Infrastructure.Services;

namespace UiTime.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ScheduleController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly IScheduleParserService _parserService;
    private readonly TimeZoneInfo _polishZone;

    public ScheduleController(AppDbContext dbContext, IScheduleParserService scheduleParserService)
    {
        _context = dbContext;
        _parserService = scheduleParserService;
        _polishZone = TimeZoneInfo.FindSystemTimeZoneById("Europe/Warsaw");
    }

    [HttpPost("upload")]
    public async Task<IActionResult> UploadSchedule(IFormFile file)
    {
        if (file == null || file.Length == 0)
            return BadRequest("File is empty or not provided.");

        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;

        if (!long.TryParse(telegramIdString, out var telegramId))
            return Unauthorized("Invalid token claims. Cannot find TelegramId.");

        var user = await _context.Users.FirstOrDefaultAsync(u => u.TelegramId == telegramId);
        if (user == null)
            return NotFound("User not found in database.");

        using var stream = file.OpenReadStream();
        var parsedLessons = _parserService.ParseSchedule(stream).ToList();

        if (!parsedLessons.Any())
            return Ok(new { Message = "No lessons found in the file." });

        var existingSubjects = await _context.Subjects.ToListAsync();
        var newLessons = new List<Lesson>();

        foreach (var parsed in parsedLessons)
        {
            var subject = existingSubjects.FirstOrDefault(s => 
                s.Name == parsed.SubjectNameRaw && s.Type == parsed.Type);

            if (subject == null)
            {
                subject = new Subject
                {
                    Name = parsed.SubjectNameRaw,
                    Type = parsed.Type,
                    HasExam = false
                };
                _context.Subjects.Add(subject);
                existingSubjects.Add(subject);
            }

            newLessons.Add(new Lesson
            {
                UserId = user.Id,
                Subject = subject,
                StartTime = parsed.StartTime,
                EndTime = parsed.EndTime,
                Location = parsed.Location,
                OnlineLink = parsed.OnlineLink
            });
        }

        var existingUserLessons = await _context.Lessons
            .Where(l => l.UserId == user.Id)
            .ToListAsync();

        _context.Lessons.RemoveRange(existingUserLessons);
        _context.Lessons.AddRange(newLessons);
        await _context.SaveChangesAsync();

        return Ok(new { Message = $"Successfully uploaded {newLessons.Count} lessons for user {user.Username}." });
    }

    [HttpGet("today")]
    public async Task<ActionResult<IEnumerable<LessonDto>>> GetTodaySchedule()
    {
        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;

        if (!long.TryParse(telegramIdString, out long telegramId))
            return Unauthorized("Invalid token claims.");

        var startOfToday = DateTime.UtcNow.Date;
        var startOfTomorrow = startOfToday.AddDays(1);

        var lessons = await _context.Lessons
            .Include(l => l.Subject)
            .Where(l => l.User.TelegramId == telegramId 
                        && l.StartTime >= startOfToday 
                        && l.StartTime < startOfTomorrow)
            .OrderBy(l => l.StartTime)
            .ToListAsync();

        var dtos = lessons.Select(l => new LessonDto(
            l.Id,
            l.Subject.Name,
            l.Subject.Type,
            TimeZoneInfo.ConvertTime(l.StartTime, _polishZone),
            TimeZoneInfo.ConvertTime(l.EndTime, _polishZone),
            l.Location,
            l.OnlineLink
        ));

        return Ok(dtos);
    }

    [HttpGet("tomorrow")]
    public async Task<ActionResult<IEnumerable<LessonDto>>> GetTomorrowSchedule()
    {
        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;

        if (!long.TryParse(telegramIdString, out long telegramId))
            return Unauthorized("Invalid token claims.");

        var startOfTomorrow = DateTime.UtcNow.Date.AddDays(1);
        var startOfDayAfterTomorrow = startOfTomorrow.AddDays(1);

        var lessons = await _context.Lessons
            .Include(l => l.Subject)
            .Where(l => l.User.TelegramId == telegramId 
                        && l.StartTime >= startOfTomorrow 
                        && l.StartTime < startOfDayAfterTomorrow)
            .OrderBy(l => l.StartTime)
            .ToListAsync();

        var dtos = lessons.Select(l => new LessonDto(
            l.Id,
            l.Subject.Name,
            l.Subject.Type,
            TimeZoneInfo.ConvertTime(l.StartTime, _polishZone),
            TimeZoneInfo.ConvertTime(l.EndTime, _polishZone),
            l.Location,
            l.OnlineLink
        ));

        return Ok(dtos);
    }

    [HttpGet("date/{startDate}/{endDate?}")]
    public async Task<ActionResult<IEnumerable<LessonDto>>> GetScheduleByDate([FromRoute] DateTime startDate, [FromRoute] DateTime? endDate)
    {
        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;

        if (!long.TryParse(telegramIdString, out long telegramId))
            return Unauthorized("Invalid token claims.");
        
        var startOfDay = startDate.Date;
        
        DateTime endOfDay;
        if (endDate.HasValue)
        {
            if (endDate.Value.Date < startOfDay)
                return BadRequest("End date cannot be earlier than start date.");
            
            endOfDay = endDate.Value.Date.AddDays(1);
        }
        else
        {
            endOfDay = startOfDay.AddDays(1);
        }

        var lessons = await _context.Lessons
            .Include(l => l.Subject)
            .Where(l => l.User.TelegramId == telegramId 
                        && l.StartTime >= startOfDay 
                        && l.StartTime < endOfDay)
            .OrderBy(l => l.StartTime)
            .ToListAsync();

        var dtos = lessons.Select(l => new LessonDto(
            l.Id,
            l.Subject.Name,
            l.Subject.Type,
            TimeZoneInfo.ConvertTime(l.StartTime, _polishZone),
            TimeZoneInfo.ConvertTime(l.EndTime, _polishZone),
            l.Location,
            l.OnlineLink
        ));

        return Ok(dtos);
    }

    [HttpGet("nearest")]
    public async Task<ActionResult<IEnumerable<LessonDto>>> GetNearestDaySchedule()
    {
        var telegramIdString = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
                               ?? User.FindFirst("sub")?.Value;

        if (!long.TryParse(telegramIdString, out long telegramId))
            return Unauthorized("Invalid token claims.");

        var now = DateTime.UtcNow;

        var nearestLesson = await _context.Lessons
            .Where(l => l.User.TelegramId == telegramId && l.StartTime >= now)
            .OrderBy(l => l.StartTime)
            .FirstOrDefaultAsync();

        if (nearestLesson == null)
            return Ok(new List<LessonDto>());

        var startOfDay = nearestLesson.StartTime.Date;
        var endOfDay = startOfDay.AddDays(1);

        var lessons = await _context.Lessons
            .Include(l => l.Subject)
            .Where(l => l.User.TelegramId == telegramId 
                        && l.StartTime >= startOfDay 
                        && l.StartTime < endOfDay)
            .OrderBy(l => l.StartTime)
            .ToListAsync();

        var dtos = lessons.Select(l => new LessonDto(
            l.Id,
            l.Subject.Name,
            l.Subject.Type,
            TimeZoneInfo.ConvertTime(l.StartTime, _polishZone),
            TimeZoneInfo.ConvertTime(l.EndTime, _polishZone),
            l.Location,
            l.OnlineLink
        ));

        return Ok(dtos);
    }
}