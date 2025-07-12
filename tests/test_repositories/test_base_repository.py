import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import Select

from app.db.repositories.base import CRUDBaseRepository
from app.db.models.usuarios import Usuario
from app.db.session import Base
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import uuid


class TestModel(Base):
    """Test model for repository testing."""
    __tablename__ = 'test_models'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    # Additional fields used in tests
    status = Column(String, nullable=True)
    company_id = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    rol = Column(String, nullable=True)


class TestCRUDBaseRepository:
    """Test suite for CRUDBaseRepository class."""

    @pytest.fixture
    def repository(self):
        """Create a repository instance for testing."""
        return CRUDBaseRepository(TestModel)

    @pytest.fixture
    def mock_result(self):
        """Create a mock result object."""
        # Create test model instances with proper attributes
        test_model1 = TestModel()
        test_model1.id = "test-id-1"
        test_model1.name = "test-name-1"
        test_model1.email = "test1@example.com"
        
        test_model2 = TestModel()
        test_model2.id = "test-id-2"
        test_model2.name = "test-name-2"
        test_model2.email = "test2@example.com"
        
        # Create properly configured mock result
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = test_model1
        mock_scalars.all.return_value = [test_model1, test_model2]
        
        result = MagicMock()
        result.scalars.return_value = mock_scalars
        return result

    @pytest.mark.asyncio
    async def test_get_success(self, repository, mock_db_session, mock_result):
        """Test successful get operation."""
        # Arrange
        mock_db_session.execute.return_value = mock_result
        test_id = "test-id-123"

        # Act
        result = await repository.get(mock_db_session, test_id)

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.first.return_value

    @pytest.mark.asyncio
    async def test_get_not_found(self, repository, mock_db_session):
        """Test get operation when record is not found."""
        # Arrange
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await repository.get(mock_db_session, "non-existent-id")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_multi_no_filters(self, repository, mock_db_session, mock_result):
        """Test get_multi without filters."""
        # Arrange
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await repository.get_multi(mock_db_session, skip=0, limit=10)

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.all.return_value

    @pytest.mark.asyncio
    async def test_get_multi_with_exact_filters(self, repository, mock_db_session, mock_result):
        """Test get_multi with exact filters."""
        # Arrange
        mock_db_session.execute.return_value = mock_result
        filters = {"name": "test", "status": "active"}

        # Act
        result = await repository.get_multi(mock_db_session, filters=filters)

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.all.return_value

    @pytest.mark.asyncio
    async def test_get_multi_with_advanced_filters_all_types(self, repository, mock_db_session, mock_result):
        """Test get_multi_with_advanced_filters with all filter types."""
        # Arrange
        mock_db_session.execute.return_value = mock_result
        exact_filters = {"company_id": "123", "status": "active"}
        ilike_filters = {"name": "%john%", "email": "%@example.com"}
        like_filters = {"description": "%important%"}

        # Act
        result = await repository.get_multi_with_advanced_filters(
            mock_db_session,
            skip=0,
            limit=50,
            exact_filters=exact_filters,
            ilike_filters=ilike_filters,
            like_filters=like_filters
        )

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.all.return_value

    @pytest.mark.asyncio
    async def test_get_multi_with_advanced_filters_ilike_only(self, repository, mock_db_session, mock_result):
        """Test get_multi_with_advanced_filters with only ilike filters."""
        # Arrange
        mock_db_session.execute.return_value = mock_result
        ilike_filters = {"display_name": "%search%"}

        # Act
        result = await repository.get_multi_with_advanced_filters(
            mock_db_session,
            ilike_filters=ilike_filters
        )

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.all.return_value

    @pytest.mark.asyncio
    async def test_get_multi_with_advanced_filters_exact_only(self, repository, mock_db_session, mock_result):
        """Test get_multi_with_advanced_filters with only exact filters."""
        # Arrange
        mock_db_session.execute.return_value = mock_result
        exact_filters = {"company_id": "123", "rol": "ADMIN"}

        # Act
        result = await repository.get_multi_with_advanced_filters(
            mock_db_session,
            exact_filters=exact_filters
        )

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.all.return_value

    @pytest.mark.asyncio
    async def test_get_multi_with_advanced_filters_empty_filters(self, repository, mock_db_session, mock_result):
        """Test get_multi_with_advanced_filters with empty filters."""
        # Arrange
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await repository.get_multi_with_advanced_filters(
            mock_db_session,
            exact_filters={},
            ilike_filters={},
            like_filters={}
        )

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.all.return_value

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_db_session):
        """Test successful create operation."""
        # Arrange
        mock_obj_in = MagicMock()
        mock_obj_in.model_dump.return_value = {"name": "test", "email": "test@example.com"}
        created_obj = TestModel()

        with patch.object(repository, 'model', return_value=created_obj) as mock_model:
            mock_model.return_value = created_obj

            # Act
            result = await repository.create(mock_db_session, mock_obj_in)

            # Assert
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_error_handling(self, repository, mock_db_session):
        """Test create operation error handling."""
        # Arrange
        mock_obj_in = MagicMock()
        mock_obj_in.model_dump.return_value = {"name": "test"}
        mock_db_session.commit.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await repository.create(mock_db_session, mock_obj_in)
        
        assert "Error al crear TestModel" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_with_dict(self, repository, mock_db_session):
        """Test update operation with dictionary input."""
        # Arrange
        db_obj = TestModel()
        update_data = {"name": "updated_name", "email": "updated@example.com"}

        # Act
        result = await repository.update(mock_db_session, db_obj, update_data)

        # Assert
        mock_db_session.add.assert_called_once_with(db_obj)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(db_obj)
        assert result == db_obj

    @pytest.mark.asyncio
    async def test_update_with_schema(self, repository, mock_db_session):
        """Test update operation with schema input."""
        # Arrange
        db_obj = TestModel()
        mock_schema = MagicMock()
        mock_schema.model_dump.return_value = {"name": "updated_name"}

        # Act
        result = await repository.update(mock_db_session, db_obj, mock_schema)

        # Assert
        mock_db_session.add.assert_called_once_with(db_obj)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(db_obj)
        assert result == db_obj

    @pytest.mark.asyncio
    async def test_remove_existing_object(self, repository, mock_db_session):
        """Test remove operation with existing object."""
        # Arrange
        test_id = "test-id"
        existing_obj = TestModel()
        
        with patch.object(repository, 'get', return_value=existing_obj):
            # Act
            result = await repository.remove(mock_db_session, test_id)

            # Assert
            mock_db_session.delete.assert_called_once_with(existing_obj)
            mock_db_session.commit.assert_called_once()
            assert result == existing_obj

    @pytest.mark.asyncio
    async def test_remove_non_existing_object(self, repository, mock_db_session):
        """Test remove operation with non-existing object."""
        # Arrange
        test_id = "non-existent-id"
        
        with patch.object(repository, 'get', return_value=None):
            # Act
            result = await repository.remove(mock_db_session, test_id)

            # Assert
            mock_db_session.delete.assert_not_called()
            mock_db_session.commit.assert_not_called()
            assert result is None

    @pytest.mark.asyncio
    async def test_get_by_field(self, repository, mock_db_session, mock_result):
        """Test get_by_field operation."""
        # Arrange
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_field(mock_db_session, "email", "test@example.com")

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.first.return_value

    @pytest.mark.asyncio
    async def test_get_multi_by_field_without_pagination(self, repository, mock_db_session, mock_result):
        """Test get_multi_by_field operation without pagination parameters."""
        # Arrange
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await repository.get_multi_by_field(mock_db_session, "company_id", "123")

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.all.return_value

    @pytest.mark.asyncio
    async def test_get_multi_by_field_with_pagination(self, repository, mock_db_session, mock_result):
        """Test get_multi_by_field operation with pagination parameters."""
        # Arrange
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await repository.get_multi_by_field(
            mock_db_session, 
            "company_id", 
            "123", 
            skip=10, 
            limit=20
        )

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.all.return_value

    @pytest.mark.asyncio
    async def test_get_multi_by_filters(self, repository, mock_db_session, mock_result):
        """Test get_multi_by_filters operation with SQLAlchemy filters."""
        # Arrange
        mock_db_session.execute.return_value = mock_result
        filters = [TestModel.name == "test", TestModel.email.like("%@example.com")]

        # Act
        result = await repository.get_multi_by_filters(
            mock_db_session,
            filters,
            skip=0,
            limit=50
        )

        # Assert
        mock_db_session.execute.assert_called_once()
        assert result == mock_result.scalars.return_value.all.return_value 