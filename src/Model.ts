

export class Tag {
    private name: string;
    private value?: string;
}

export class Database {
    private dir: File;
}

export class Entry {
    private file: File;
    private tags: Tag[];
}
