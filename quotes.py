# -*- coding: utf-8 -*-

randoms = [['Трудно найти слова, когда действительно есть, что сказать.', 'Три Товарища', 'Эрих_Мария_Ремарк',
            "https://librebook.me/three_comrades"],
           ['— Любовь. Я оттого и не люблю этого слова, что оно для меня слишком много значит, больше гораздо, чем вы можете понять.',
            'Анна Каренина', 'Лев_Николаевич_Толстой', "https://librebook.me/anna_karenina"],
           ['Пусть Бог наказывает злых людей, мы же должны учиться прощать', 'Грозовой перевал', 'Эмили_Бронте', 'https://librebook.me/wuthering_heights'],
           ['Излишняя мягкость порой причиняет зло.', 'Грозовой перевал', 'Эмили_Бронте', 'https://librebook.me/wuthering_heights'],
           ['Я настолько горда, что никогда не позволю себе любить человека, который меня не любит.', 'Анна Каренина',
            'Лев_Николаевич_Толстой', "https://librebook.me/anna_karenina"],
           ['Если добро имеет причину, оно уже не добро; если оно имеет последствие – награду, оно тоже не добро. Стало быть, добро вне цепи причин и следствий.',
            'Анна Каренина', 'Лев_Николаевич_Толстой', "https://librebook.me/anna_karenina"],
           ['Какой-то математик сказал, что наслаждение не в открытии истины, но в ее поиске.', 'Анна Каренина',
            'Лев_Николаевич_Толстой', "https://librebook.me/anna_karenina"],
           ['Копаясь в своей душе, мы часто выкапываем такое, что там лежало бы незаметно', 'Анна Каренина',
            'Лев_Николаевич_Толстой',
            "https://librebook.me/anna_karenina"],
           ["Забавная штука – жизнь, таинственная, с безжалостной логикой преследующая ничтожные цели. Самое большее, что может получить от неё человек, это – познание себя самого, которое приходит слишком поздно и приносит вечные сожаления.",
            "Сердце тьмы", "Джозеф_Конрад", "https://librebook.me/heart_of_darkness"],
           ['…вся прелесть прошлого в том, что оно – прошлое.', 'Портрет Дориана Грея', 'Оскар_Уайльд',
            'https://librebook.me/the_picture_of_dorian_gray'],
           ['Каждый живет, как хочет, и расплачивается за это сам.', 'Портрет Дориана Грея', 'Оскар_Уайльд',
            'https://librebook.me/the_picture_of_dorian_gray'],
           ['Влюбленность начинается с того, что человек обманывает себя, а кончается тем, что он обманывает другого. Это и принято называть романом.',
            'Портрет Дориана Грея', 'Оскар_Уайльд', 'https://librebook.me/the_picture_of_dorian_gray'],
           ['Быть вместе — значит чувствовать себя так же непринуждённо, как в одиночестве, и так же весело, как в обществе.',
            'Джейн Эйр', 'Шарлотта_Бронте', 'https://librebook.me/jane_eyre'],
           ['Тот, кто идет по живописной местности к эшафоту, не смотрит на цветы, улыбающиеся ему по пути. Он думает о топоре и плахе, о страшном ударе, сокрушающем кости и жилы, и о могиле в конце пути.',
            'Джейн Эйр', 'Шарлотта_Бронте', 'https://librebook.me/jane_eyre'],
           ['Уверен, все мы чокнутые, только каждый по-своему.', 'Безмолвный пациент', 'Алекс_Михаэлидес',
            'https://librebook.me/bezmolvnyi_pacient'],
           ['Он знал, что в жизни поневоле приходится, как говорят, тереться между людей, а так как трение замедляет движение, то он держался в стороне от всех.',
            'Вокруг света за восемьдесят дней', 'Жюль_Верн', 'https://librebook.me/around_the_world_in_eighty_days'],
           ['...если бы вы мне сказали одно слово одно только слово - я бы осталась. Вы его не сказали. Видно, так лучше...',
            'Ася', 'Иван_Сергеевич_Тургенев', 'https://librebook.me/asia'],
           ['Вы находите мое поведение неприличным, – казалось, говорило ее лицо, – все равно: я знаю, вы мной любуетесь.',
            'Ася', 'Иван_Сергеевич_Тургенев', 'https://librebook.me/asia'],
           ['Есть на свете такие счастливые лица: глядеть на них всякому любо, точно они греют вас или гладят.', 'Ася',
            'Иван_Сергеевич_Тургенев', 'https://librebook.me/asia'],
           ['Жизнь слишком коротка, и не стоит тратить ее на то, чтобы лелеять в душе вражду или запоминать обиды.',
            'Джейн Эйр', 'Шарлотта_Бронте', 'https://librebook.me/jane_eyre'],
           ['Ты навсегда в ответе за всех, кого приручил.', 'Маленький Принц', 'Антуан_де_Сент_Экзюпери', 'https://librebook.me/the_little_prince'],
           ['— Тогда суди сам себя, — сказал король. — Это самое трудное. Себя судить куда трудней, чем других. Если ты сумеешь правильно судить себя, значит, ты поистине мудр.',
            'Маленький Принц', 'Антуан_де_Сент_Экзюпери', 'https://librebook.me/the_little_prince'],
           ['— А что надо сделать, чтобы шляпа упала? — спросил он.\nНо честолюбец не слышал. Тщеславные люди глухи ко всему, кроме похвал.',
            'Маленький Принц', 'Антуан_де_Сент_Экзюпери', 'https://librebook.me/the_little_prince'],
           ['Ведь все взрослые сначала были детьми, только мало кто из них об этом помнит.','Маленький Принц', 'Антуан_де_Сент_Экзюпери',
            'https://librebook.me/the_little_prince'],
           ['Ничто никогда не бывает зря.', 'Детектив', 'Артур_Хейли', 'https://librebook.me/detective'],
           ['— Мой дорогой друг, кто вам позволит? \n— Это не главное. Главное — кто меня остановит?', 'Источник', 'Айн_Рэнд',
            'https://librebook.me/the_fountainhead'],
           ['Счастливые часов не наблюдают.', 'Горе от ума', 'Александр_Грибоедов', 'https://librebook.me/gore_ot_uma__sbornik'],
           ['Кто слишком часто оглядывается назад, легко может споткнуться и упасть.', 'Триумфальная Арка', 'Эрих_Мария_Ремарк',
            'https://librebook.me/arch_of_triumph'],
           ['Сражение выигрывает тот, кто твердо решил его выиграть!', 'Война и мир', 'Лев_Толстой', 'https://librebook.me/voina_i_mir'],
           ['Тот, кто задает вопрос, глупец в течение пяти минут, тот, кто его не задает, глупец всю свою жизнь.', 'Муравьи',
            'Бернард_Вербер', 'https://avidreaders.ru/book/muravi.html'],
           ['Есть преступления хуже, чем сжигать книги. Например — не читать их.', '451 градус по Фаренгейту', 'Рэй_Бредберри',
            'https://librebook.me/fahrenheit_451'],
           ['Музыка — прекрасный способ стирания мыслей, плохих и не очень, самый лучший и самый давний.', 'Дом, в котором...',
            'Мариам_Петросян', 'https://librebook.me/dom__v_kotorom____mariam_petrosian'],
           ['Найди свою шкуру, Македонский, найди свою маску, говори о чём-нибудь, делай что-нибудь, тебя должны чувствовать, понимаешь? Или ты исчезнешь.',
            'Дом, в котором...', 'Мариам_Петросян', 'https://librebook.me/dom__v_kotorom____mariam_petrosian'],
           ['— Я красивый, — сказал урод и заплакал...\n— А я урод, — сказал другой урод и засмеялся...',
            'Дом, в котором...', 'Мариам_Петросян', 'https://librebook.me/dom__v_kotorom____mariam_petrosian'],
           ['Путь к сердцу женщины лежит через смех.', 'Дом, в котором...', 'Мариам_Петросян', 'https://librebook.me/dom__v_kotorom____mariam_petrosian'],
           ['— Просто хочется, чтобы он полюбил этот мир. Хоть немного. Насколько это будет в моих силах.\n— Он полюбит тебя. Только тебя. И ты для него будешь весь чёртов мир.',
            'Дом, в котором...', 'Мариам_Петросян', 'https://librebook.me/dom__v_kotorom____mariam_petrosian'],
           ['Советы принимай от всех дающих,\nНо собственное мненье береги.', 'Гамлет', 'Уильям_Шекспир',
            'https://librebook.me/the_tragical_historie_of_hamlet__prince_of_denmarke'],
           ['Слова парят, а чувства книзу гнут.\nА слов без чувств вверху не признают.', 'Гамлет', 'Уильям_Шекспир',
            'https://librebook.me/the_tragical_historie_of_hamlet__prince_of_denmarke'],
           ['Краткость ест душа ума,\nА многословье – тело и прикрасы.', 'Гамлет', 'Уильям_Шекспир',
            'https://librebook.me/the_tragical_historie_of_hamlet__prince_of_denmarke'],
           ['Так создан мир: что живо, то умрет\nИ вслед за жизнью в вечность отойдет.', 'Гамлет', 'Уильям_Шекспир',
            'https://librebook.me/the_tragical_historie_of_hamlet__prince_of_denmarke'],
           ['...чем дольше я живу, тем яснее понимаю, что главное в жизни — это твердо знать, чего ты хочешь, и не позволять сбить себя с толку тем, кому кажется, будто они знают лучше.',
            'Дживс, Вы гений!', 'Пэлем_Гринвел_Вудхауз', 'https://librebook.me/thank_you__jeeves'],
           ['Если ты направляешься к цели и станешь дорогою останавливаться, чтобы швырять камнями во всякую лающую на тебя собаку, то никогда не дойдёшь до цели.',
            'Дневник писателя', 'Фёдор_Достоевский', 'https://librebook.me/dnevnik_pisatelia_1876'],
           ['...человек никогда не присутствует там, где он на самом деле находится. Он вечно копается в прошлом или заглядывает в будущее, а просто спокойно побыть в настоящем — такая редкость.',
            'Есть, молиться, любить', 'Элизабет_Гилберт', 'https://librebook.me/eat__pray__love'],
           ['Не имеет значения, что думают другие — поскольку они в любом случае что-нибудь подумают. Так что расслабься.',
            'Мактуб', 'Пауло_Коэльо', 'https://librebook.me/maktub'],
           ['Нет времени? Серьёзно? Это желания нет, а время есть всегда.', 'Стихотворения', 'Сергей_Есенин', 'https://librebook.me/tom_1__stihotvoreniia'],
           ['Ресурсы, которые вам необходимы для того, чтобы что-то изменить в своей жизни, находятся в вас самих и доступны прямо сейчас.',
            'Разбуди в себе исполина', 'Энтони_Робертс', 'https://avidreaders.ru/book/razbudi-v-sebe-ispolina.html'],
           ['Жизнь — это поезд, займи свое место.', 'Бегущий за ветром', 'Халед_Хоссейни', 'https://librebook.me/the_kite_runner'],
           ['Просто беда с ними, с откровенными, открытыми людьми. Они думают, что и все остальные - такие же.', 'Бегущий за ветром',
            'Халед_Хоссейни', 'https://librebook.me/the_kite_runner'],
           ['...обрести и вновь потерять всегда больнее, чем не иметь вовсе.', 'Бегущий за ветром', 'Халед_Хоссейни',
            'https://librebook.me/the_kite_runner'],
           ['Счастье робкому не даётся, а кто рискует — тот часто выигрывает!', 'Рейнеке-лис', 'Иоганн_Вольфганг_Гёте',
            'https://librebook.me/reineke_lis'],
           ['К чему печалиться, если все можно еще поправить? И к чему печалиться, если ничего уже поправить нельзя?',
            'Книга радости', 'Далай_Лама', 'https://avidreaders.ru/book/kniga-radosti-kak-byt-schastlivym-v.html'],
           ['Даже остановившиеся часы два раза в день показывают точное время.', 'Зеленая миля', 'Стивен_Кинг',
            'https://librebook.me/the_green_mile'],
           ['Никто из нас не жаловался – бесполезно. Планета вращается, знаете ли. Можно вращаться вместе с ней, а можно зацепиться за что-то и протестовать, но тогда тебя свалит с ног.',
            'Зеленая миля', 'Стивен_Кинг', 'https://librebook.me/the_green_mile'],
           ['Машина времени есть у каждого из нас: то, что переносит в прошлое — воспоминания; то, что уносит в будущее — мечты',
            'Машина времени', 'Герберт_Уэллс', 'https://librebook.me/the_time_machine'],
           ['Но когда-нибудь ты дорастёшь до такого дня, когда вновь начнёшь читать сказки.', 'Хроники Нарнии',
            'Клайв_Льюис','https://librebook.me/the_lion__the_witch_and_the_wardrobe'],
           ['Детство мы тратим впустую, желая стать взрослыми, а когда вырастем, тратим всю жизнь на то, чтоб не состариться',
             'Хроники Нарнии', 'Клайв_Льюис','https://librebook.me/the_lion__the_witch_and_the_wardrobe'],
           ['Кто жил и мыслил, тот не может\nВ душе не презирать людей...', 'Евгений Онегин','Александр_Сергеевич_Пушкин',
            'https://librebook.me/evgenii_onegin'],
           ['Любовью шутит сатана.', 'Евгений Онегин', 'Александр_Сергеевич_Пушкин', 'https://librebook.me/evgenii_onegin'],
           ['Все предрассудки истребя,\nМы почитаем всех нулями,\nА единицами – себя.',
            'Евгений Онегин', 'Александр_Сергеевич_Пушкин', 'https://librebook.me/evgenii_onegin'],
           [" с той минуты, когда я вышел из опеки родных, я стал наслаждаться бешено всеми удовольствиями, которые можно достать за деньги, и, разумеется, удовольствия эти мне опротивели.",
            "Герой нашего времени", "Михаил_Юрьевич_Лермонтов", "https://librebook.me/geroi_nashego_vremeni_lermontov_mihail_iurevich"],
           ["...любовь дикарки немногим лучше, чем любовь знатной барыни; невежество и простосердечие одной так же надоедают, как и кокетство другой...",
            "Герой нашего времени", "Михаил_Юрьевич_Лермонтов", "https://librebook.me/geroi_nashego_vremeni_lermontov_mihail_iurevich"],
           ["Я никогда сам не открываю моих тайн, а ужасно люблю, чтоб их отгадывали, потому что таким образом я всегда могу при случае от них отпереться.",
            "Герой нашего времени", "Михаил_Юрьевич_Лермонтов", "https://librebook.me/geroi_nashego_vremeni_lermontov_mihail_iurevich"],
           ["Я был готов любить весь мир, – меня никто не понял: и я выучился ненавидеть.", "Михаил_Юрьевич_Лермонтов",
            "Герой нашего времени", "https://librebook.me/geroi_nashego_vremeni_lermontov_mihail_iurevich"],
           ["И если б все люди побольше рассуждали, то убедились бы, что жизнь не стоит того, чтоб об ней так сильно заботиться.",
            "Герой нашего времени", "Михаил_Юрьевич_Лермонтов", "https://librebook.me/geroi_nashego_vremeni_lermontov_mihail_iurevich"],
           ["Мы ко всему довольно равнодушны, кроме самих себя.", "Герой нашего времени","Михаил_Юрьевич_Лермонтов",  
            "https://librebook.me/geroi_nashego_vremeni_lermontov_mihail_iurevich"],
           ['Лучший способ избавиться от врага — везде говорить о нём только хорошее. Ему это перескажут, и он уже не сможет вам вредить: вы сломили его дух. Он будет по-прежнему воевать против вас, но без особого рвения и упорства, потому что подсознательно он уже перестал вас ненавидеть. Он побежден, даже не зная о собственном поражении',
            'Признания и проклятия', 'Эмиль_Мишель_Чоран', 'https://libking.ru/books/sci-/sci-philosophy/216242-emil-choran-priznaniya-i-proklyatiya.html'],
           ['— А как же ты можешь разговаривать, если у тебя нет мозгов? — спросила Дороти. \n— Не знаю, — ответил Чучело, — но те, у кого нет мозгов, очень любят разговаривать',
            'Волшебник из страны Оз', 'Лаймен_Фрэнк_Баум', 'https://librebook.me/dorothy_and_the_wizard_in_oz'],
           ['Без зимних морозов нет радости от весеннего тепла. И, кстати, морозами тоже можно наслаждаться',
            'Фантомная боль', 'Олег_Рой', 'https://bookshake.net/b/fantomnaya-bol-oleg-yurevich-roy'],
           ['Счастье, говоришь? Какой может быть разговор о счастье, если вы все – ну большинство – предаетесь либо воспоминаниям, либо мечтам. А того, что сию минуту, не то что не цените, вообще не замечаете.',
            'Фантомная боль', 'Олег_Рой', 'https://bookshake.net/b/fantomnaya-bol-oleg-yurevich-roy'],
           ]
users_queue = []
