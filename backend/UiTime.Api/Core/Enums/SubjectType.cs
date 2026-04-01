namespace UiTime.Api.Core.Entities;

public enum SubjectType
{
    // Podstawowe
    Lecture,           // Wykład
    Tutorial,          // Ćwiczenia
    Laboratory,        // Laboratorium
    Seminar,           // Seminarium
    Project,           // Projekt
    Konwersatorium,    // Konwersatorium

    // Medyczne / praktyczne
    Clinical,          // Zajęcia kliniczne
    Practical,         // Zajęcia praktyczne
    Internship,        // Staż / Praktyki
    Rotation,          // Rotacja kliniczna
    Simulation,        // Symulacja medyczna

    // Interaktywne / specjalne formy
    Workshop,          // Warsztaty
    CaseStudy,         // Analiza przypadków
    Discussion,        // Dyskusja

    // Organizacyjne / dodatkowe
    Consultation,      // Konsultacje
    Colloquium,        // Kolokwium
    Exam,              // Egzamin
    Credit,            // Zaliczenie

    // Online / indywidualne
    ELearning,         // E-learning
    SelfStudy,         // Samokształcenie

    // Naukowe
    Research,          // Badania naukowe
    Thesis,             // Praca dyplomowa
    Other
}