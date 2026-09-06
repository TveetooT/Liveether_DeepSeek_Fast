-- Таблица users
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    name TEXT,
    age INT,
    univer TEXT,
    about TEXT,
    requirements TEXT,
    region TEXT,
    city TEXT,
    form BOOLEAN DEFAULT false,
    action TEXT,
    root BOOLEAN DEFAULT false,
    banned BOOLEAN DEFAULT false,
    reports INT DEFAULT 0,
    views_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP
);

-- Таблица views
CREATE TABLE IF NOT EXISTS views (
    user_id BIGINT,
    viewed_user_id BIGINT,
    state TEXT DEFAULT 'unseen',
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, viewed_user_id)
);

-- Функция get_unseen_users
CREATE OR REPLACE FUNCTION get_unseen_users(p_user_id BIGINT, p_city TEXT)
RETURNS TABLE (
    user_id BIGINT,
    username TEXT,
    name TEXT,
    age INT,
    univer TEXT,
    about TEXT,
    requirements TEXT,
    region TEXT,
    city TEXT,
    views_count INT,
    last_active TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.user_id, u.username, u.name, u.age, u.univer, u.about, u.requirements, u.region, u.city, u.views_count, u.last_active
    FROM users u
    WHERE u.city = p_city
      AND u.user_id != p_user_id
      AND u.form = true
      AND u.banned = false
      AND NOT EXISTS (
          SELECT 1 FROM views v
          WHERE v.user_id = p_user_id AND v.viewed_user_id = u.user_id
      );
END;
$$ LANGUAGE plpgsql;

-- Функция для пересоздания БД (опционально)
CREATE OR REPLACE FUNCTION recreate_database()
RETURNS VOID AS $$
BEGIN
    DROP TABLE IF EXISTS views CASCADE;
    DROP TABLE IF EXISTS users CASCADE;
    -- создать заново (аналогично CREATE TABLE выше)
END;
$$ LANGUAGE plpgsql;