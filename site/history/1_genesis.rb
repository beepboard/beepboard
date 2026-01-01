Sequel.migration do
    up do
        create_table :tokens do
            String      :id,           primary_key: true
            foreign_key :user, :users, null: false
            Integer     :permissions,  null: false
            DateTime    :created,      null: false
        end

        create_table :users do
            primary_key :id
            String :email,    null: false
            String :username, null: false
            String :password, null: false
        end

        create_table :links do
            primary_key :id
            Integer :views, default: 0
            String :url, null: false
        end
    end
end
