create table status_type (
    status_type varchar not null primary key
);

insert into status_type values ('todo');
insert into status_type values ('in_progress');
insert into status_type values ('done');

create table resource (
    id bigint not null primary key,
    name varchar not null,
    email varchar not null
);

create table task (
    id bigint not null primary key,
    status_type varchar not null references status_type,
    assigned_to_resource_id bigint not null references resource,
    created_date datetime not null,
    created_by_resource_id bigint not null references resource
);
create table related_task_type (
    related_task_type varchar not null primary key
);

insert into related_task_type values ('blocks');
insert into related_task_type values ('is_blocked_by');
insert into related_task_type values ('duplicates');
insert into related_task_type values ('is_a_duplicate_of');
insert into related_task_type values ('related');

create table related_task (
    id bigint not null primary key,
    task1_id bigint not null references task,
    task2_id bigint not null references task,
    related_task_type varchar not null references related_task_type
);