/** Sample file with Interface Segregation violation. */
export interface Worker {
    work(): void;
    eat(): void;
    sleep(): void;
    attendMeeting(): void;
    writeReport(): void;
    code(): void;
    test(): void;
    deploy(): void;
    monitor(): void;
    debug(): void;
    optimize(): void;
    document(): void;
    review(): void;
    plan(): void;
    estimate(): void;
    present(): void;
    negotiate(): void;
    hire(): void;
    fire(): void;
    promote(): void;
    manageBudget(): void;
    approveLeaves(): void;
    conductInterview(): void;
}
